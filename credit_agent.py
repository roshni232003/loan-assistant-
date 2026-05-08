"""
agents/master_agent.py — The BOSS: Orchestrates all 6 sub-agents using LangChain
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

from agents.sales_agent        import SalesAgent
from agents.worker_agent       import WorkerAgent
from agents.verification_agent import VerificationAgent
from agents.credit_agent       import CreditRiskAgent
from agents.approval_agent     import ApprovalAgent
from agents.letter_agent       import LetterAgent

load_dotenv()


# ─────────────────────────────────────────────
#  Conversation Stages
# ─────────────────────────────────────────────
STAGE_GREETING      = "greeting"
STAGE_PRODUCT_INFO  = "product_info"
STAGE_COLLECTING    = "collecting"
STAGE_VERIFICATION  = "verification"
STAGE_CREDIT_CHECK  = "credit_check"
STAGE_DECISION      = "decision"
STAGE_LETTER        = "letter"
STAGE_DONE          = "done"


class MasterAgent:
    """
    The central orchestrator that:
    1. Maintains conversation state and stage
    2. Routes user messages to the correct sub-agent
    3. Uses LangChain + OpenAI for natural language understanding
    4. Drives the loan workflow end-to-end
    """

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.stage      = STAGE_GREETING

        # Sub-agents
        self.sales_agent    = SalesAgent()
        self.worker_agent   = WorkerAgent()
        self.verif_agent    = VerificationAgent()
        self.credit_agent   = CreditRiskAgent()
        self.approval_agent = ApprovalAgent()
        self.letter_agent   = LetterAgent()

        # LangChain LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.4,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        # Conversation memory
        self.memory   = ConversationBufferMemory(return_messages=True)
        self.history  = []    # raw list for FastAPI

        # Results cache
        self.kyc_result    = None
        self.credit_result = None
        self.approval_result = None

    # ─────────────────────────────────────────
    #  PUBLIC: Main entry point
    # ─────────────────────────────────────────
    def chat(self, user_message: str) -> str:
        """Process one user message and return the assistant's reply."""
        self.history.append({"role": "user", "content": user_message})

        response = self._route(user_message)

        self.history.append({"role": "assistant", "content": response})
        return response

    # ─────────────────────────────────────────
    #  ROUTING: Stage-based dispatcher
    # ─────────────────────────────────────────
    def _route(self, msg: str) -> str:
        msg_lower = msg.lower().strip()

        # ── Stage: Greeting ──────────────────
        if self.stage == STAGE_GREETING:
            self.stage = STAGE_PRODUCT_INFO
            return self.sales_agent.get_greeting()

        # ── Stage: Product Info ──────────────
        if self.stage == STAGE_PRODUCT_INFO:
            # Check if user wants to proceed
            if any(w in msg_lower for w in ["yes", "proceed", "apply", "start", "ok", "sure", "let's go"]):
                self.stage = STAGE_COLLECTING
                return (
                    "Perfect! Let's get started with your application. 🚀\n\n"
                    "I'll ask you a few quick questions. Please answer each one honestly.\n\n"
                    + self.worker_agent.next_question()
                )
            elif any(w in msg_lower for w in ["no", "not", "later", "cancel"]):
                return self.sales_agent.handle_hesitation()
            else:
                # Detect loan type mentioned
                for loan_type in ["home", "personal", "education", "business"]:
                    if loan_type in msg_lower:
                        return self.sales_agent.explain_product(loan_type)
                # Handle general queries
                return self.sales_agent.handle_query(msg)

        # ── Stage: Data Collection ───────────
        if self.stage == STAGE_COLLECTING:
            result = self.worker_agent.fill_field(msg)

            if self.worker_agent.is_complete():
                self.stage = STAGE_VERIFICATION
                summary = self.worker_agent.get_summary()
                return (
                    f"{summary}\n\n"
                    "---\n"
                    "✅ All details collected! Now proceeding to **KYC Verification**...\n\n"
                    + self._run_verification()
                )
            return result

        # ── Stage: Verification ──────────────
        if self.stage == STAGE_VERIFICATION:
            # User confirmed / retried KYC
            return self._run_verification()

        # ── Stage: Credit Check ──────────────
        if self.stage == STAGE_CREDIT_CHECK:
            return self._run_credit_check()

        # ── Stage: Decision ──────────────────
        if self.stage == STAGE_DECISION:
            return self._run_approval()

        # ── Stage: Letter ────────────────────
        if self.stage == STAGE_LETTER:
            return self._generate_letter()

        # ── Stage: Done ──────────────────────
        if self.stage == STAGE_DONE:
            return self._handle_post_approval(msg)

        return self._llm_fallback(msg)

    # ─────────────────────────────────────────
    #  PIPELINE STEPS
    # ─────────────────────────────────────────
    def _run_verification(self) -> str:
        data = self.worker_agent.data
        self.kyc_result = self.verif_agent.verify(
            pan=data.pan_number or "",
            aadhaar=data.aadhaar_number or "",
            name=data.name or ""
        )
        msg = self.verif_agent.format_result_message(self.kyc_result)

        if self.kyc_result["kyc_passed"]:
            self.stage = STAGE_CREDIT_CHECK
            return msg + "\n\n" + self._run_credit_check()
        else:
            return msg + "\n\nPlease correct your details and try again."

    def _run_credit_check(self) -> str:
        data = self.worker_agent.data
        self.credit_result = self.credit_agent.assess_risk({
            "monthly_income":   data.monthly_income,
            "loan_amount":      data.loan_amount,
            "loan_tenure":      data.loan_tenure,
            "age":              data.age,
            "existing_loans":   data.existing_loans,
            "employment_years": data.employment_years,
            "employment_type":  data.employment_type,
        })
        report = self.credit_agent.format_report(self.credit_result)
        self.stage = STAGE_DECISION
        return report + "\n\n" + self._run_approval()

    def _run_approval(self) -> str:
        data = self.worker_agent.data
        self.approval_result = self.approval_agent.decide(
            credit_result  = self.credit_result,
            kyc_result     = self.kyc_result,
            customer_data  = data.model_dump()
        )
        msg = self.approval_result["message"]

        if self.approval_result["decision"] == "APPROVED":
            self.stage = STAGE_LETTER
            return msg + "\n\n" + self._generate_letter()
        else:
            self.stage = STAGE_DONE
            return msg

    def _generate_letter(self) -> str:
        data   = self.worker_agent.data
        result = self.letter_agent.generate(
            customer_data  = data.model_dump(),
            credit_result  = self.credit_result
        )
        self.stage = STAGE_DONE
        return result["message"]

    def _handle_post_approval(self, msg: str) -> str:
        return (
            "😊 Is there anything else I can help you with?\n\n"
            "You can:\n"
            "   • Ask about your loan details\n"
            "   • Start a new application\n"
            "   • Contact support: support@svufinance.ac.in\n\n"
            "Thank you for choosing SVU Finance! 🏦"
        )

    # ─────────────────────────────────────────
    #  LLM FALLBACK: For unexpected inputs
    # ─────────────────────────────────────────
    def _llm_fallback(self, msg: str) -> str:
        """Use OpenAI to handle unrecognized messages gracefully."""
        try:
            system = SystemMessage(content=(
                "You are a friendly AI loan assistant for SVU Finance. "
                "You help customers apply for loans. Be concise, polite, and professional. "
                "Always guide customers back to the loan application process."
            ))
            human = HumanMessage(content=msg)
            response = self.llm.invoke([system] + self._build_history() + [human])
            return response.content
        except Exception:
            return (
                "I'm here to help you with your loan application! 😊\n"
                "Could you please clarify what you'd like to do? "
                "Type 'apply' to start a new application."
            )

    def _build_history(self):
        msgs = []
        for m in self.history[-6:]:  # last 3 turns
            if m["role"] == "user":
                msgs.append(HumanMessage(content=m["content"]))
            else:
                msgs.append(AIMessage(content=m["content"]))
        return msgs

    def reset(self):
        """Reset the agent for a fresh conversation."""
        self.__init__(self.session_id)
