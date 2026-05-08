"""
agents/sales_agent.py — Greets customer, explains loan products, builds rapport
"""

LOAN_PRODUCTS = {
    "personal": {
        "name": "Personal Loan",
        "min_amount": 50000,
        "max_amount": 2000000,
        "min_tenure": 12,
        "max_tenure": 60,
        "interest_rate": "10.5% – 14% p.a.",
        "features": ["No collateral needed", "Quick disbursal in 48hrs", "Flexible EMI options"]
    },
    "home": {
        "name": "Home Loan",
        "min_amount": 500000,
        "max_amount": 50000000,
        "min_tenure": 60,
        "max_tenure": 300,
        "interest_rate": "8.5% – 10% p.a.",
        "features": ["Low interest rates", "Up to 25 years tenure", "Tax benefits under 80C"]
    },
    "education": {
        "name": "Education Loan",
        "min_amount": 100000,
        "max_amount": 2000000,
        "min_tenure": 12,
        "max_tenure": 84,
        "interest_rate": "9% – 12% p.a.",
        "features": ["Moratorium period available", "Covers tuition + living expenses", "No collateral up to ₹7.5L"]
    },
    "business": {
        "name": "Business Loan",
        "min_amount": 100000,
        "max_amount": 5000000,
        "min_tenure": 12,
        "max_tenure": 60,
        "interest_rate": "12% – 16% p.a.",
        "features": ["Minimal documentation", "Collateral-free", "Overdraft facility available"]
    }
}


class SalesAgent:
    """
    Handles the greeting, product explanation, and rapport-building phase.
    Convinces the customer to proceed with the application.
    """

    def get_greeting(self) -> str:
        return (
            "👋 **Welcome to SVU Finance — AI Loan Assistant!**\n\n"
            "Hello! I'm your personal AI loan advisor. I'm here to help you get the best loan "
            "tailored to your needs — quickly and hassle-free! 🏦\n\n"
            "At SVU Finance, we offer:\n"
            "   🏠 Home Loans\n"
            "   🎓 Education Loans\n"
            "   💼 Business Loans\n"
            "   💳 Personal Loans\n\n"
            "**What type of loan are you looking for today?**\n"
            "_(Just type the name, e.g. 'Personal Loan' or 'Home Loan')_"
        )

    def explain_product(self, loan_type: str) -> str:
        key = loan_type.lower().replace(" loan", "").strip()
        product = LOAN_PRODUCTS.get(key)

        if not product:
            key = "personal"
            product = LOAN_PRODUCTS["personal"]

        features_str = "\n".join([f"   ✅ {f}" for f in product["features"]])

        return (
            f"🌟 **Great choice! Here's what our {product['name']} offers:**\n\n"
            f"💰 Loan Amount:   ₹{product['min_amount']:,} – ₹{product['max_amount']:,}\n"
            f"📅 Tenure:        {product['min_tenure']} – {product['max_tenure']} months\n"
            f"📊 Interest Rate: {product['interest_rate']}\n\n"
            f"**Why choose us?**\n{features_str}\n\n"
            f"🚀 **The entire process is 100% digital — no branch visits needed!**\n\n"
            "Shall we proceed with your application? Just say **'Yes'** and I'll guide you step by step!"
        )

    def handle_hesitation(self) -> str:
        return (
            "😊 I understand — taking a loan is a big decision! Let me reassure you:\n\n"
            "   🔒 Your data is 100% secure and encrypted\n"
            "   📋 Checking eligibility does NOT affect your credit score\n"
            "   ⚡ The whole process takes less than 10 minutes\n"
            "   ❌ You can cancel anytime before disbursement\n\n"
            "Thousands of customers have trusted SVU Finance! Would you like to check "
            "your eligibility now? It's completely free! 😊"
        )

    def handle_query(self, query: str) -> str:
        q = query.lower()
        if "interest" in q or "rate" in q:
            return (
                "📊 Our interest rates are among the lowest in the market:\n"
                "   • Personal Loan:  10.5% – 14% p.a.\n"
                "   • Home Loan:       8.5% – 10% p.a.\n"
                "   • Education Loan:  9%   – 12% p.a.\n"
                "   • Business Loan:  12%   – 16% p.a.\n\n"
                "Your final rate depends on your credit score. Higher score = lower rate! 🎯"
            )
        elif "document" in q or "kyc" in q:
            return (
                "📄 Documents needed are minimal:\n"
                "   • PAN Card\n"
                "   • Aadhaar Card\n"
                "   • Latest 3-month salary slips (for salaried)\n"
                "   • Bank statements (last 6 months)\n\n"
                "Everything is digital — just share the numbers and we verify instantly!"
            )
        elif "time" in q or "fast" in q or "quick" in q:
            return (
                "⚡ Super fast! Here's the timeline:\n"
                "   ✅ Application:    5–10 minutes\n"
                "   ✅ KYC Verify:     Instant\n"
                "   ✅ Credit Check:   30 seconds\n"
                "   ✅ Decision:       Immediate\n"
                "   ✅ Disbursal:      Within 48 hours of approval\n"
            )
        else:
            return (
                "Great question! Our team is always here to help. "
                "Shall we start your loan application? It only takes a few minutes! 😊"
            )
