"""
Sample newsletter data for testing.

This module contains realistic newsletter samples for testing the email
processing pipeline.
"""

from typing import Any, Dict, List

# TLDR Newsletter Sample
TLDR_NEWSLETTER = {
    "uid": "001",
    "subject": "TLDR - Fri, Jan 5, 2024",
    "sender": "tldr@tldrnewsletter.com",
    "date": "Fri, 05 Jan 2024 06:00:00 +0000",
    "content_type": "text/html",
    "body": """
    <html>
    <body>
    <div class="header">
        <h1>TLDR</h1>
        <p>Friday, January 5, 2024</p>
    </div>
    
    <div class="section">
        <h2>🚀 Tech</h2>
        <div class="article">
            <h3>OpenAI launches GPT Store</h3>
            <p>OpenAI has officially launched the GPT Store, allowing users to 
            discover and share custom ChatGPT versions. The store features 
            trending GPTs across categories like productivity, education, and 
            lifestyle.</p>
            <a href="#" class="read-more">Read more</a>
        </div>
        
        <div class="article">
            <h3>Apple Vision Pro launch date confirmed</h3>
            <p>Apple has confirmed that Vision Pro will launch in early February 2024, starting at $3,499. Pre-orders begin January 19th with availability in US Apple Stores.</p>
            <a href="#" class="read-more">Read more</a>
        </div>
    </div>
    
    <div class="section">
        <h2>💰 Startups</h2>
        <div class="article">
            <h3>AI startup raises $50M Series B</h3>
            <p>Anthropic competitor Claude AI has raised $50M in Series B funding to advance constitutional AI research and compete with OpenAI's ChatGPT.</p>
            <a href="#" class="read-more">Read more</a>
        </div>
    </div>
    </body>
    </html>""",
}


# Deep Learning Weekly Sample
DEEP_LEARNING_WEEKLY = {
    "uid": "002",
    "subject": "Deep Learning Weekly #156 - Transformer Innovations",
    "sender": "deeplearningweekly@gmail.com",
    "date": "Sun, 07 Jan 2024 20:00:00 +0000",
    "content_type": "text/html",
    "body": """
    <html>
    <body>
    <div class="newsletter-header">
        <h1>Deep Learning Weekly</h1>
        <h2>Issue #156 - Transformer Innovations</h2>
    </div>
    
    <div class="research-section">
        <h2>📚 Research Papers</h2>
        
        <div class="paper">
            <h3>Mamba: Linear-Time Sequence Modeling with Selective State Spaces</h3>
            <p><strong>Authors:</strong> Gu, A., & Dao, T.</p>
            <p><strong>Abstract:</strong> We introduce Mamba, a new architecture that achieves linear scaling in sequence length while maintaining the modeling power of Transformers. The key innovation is selective state spaces that can focus on relevant parts of long sequences.</p>
            <p><strong>Key Findings:</strong></p>
            <ul>
                <li>Achieves linear O(n) complexity vs O(n²) for Transformers</li>
                <li>Outperforms Transformers on sequences longer than 2K tokens</li>
                <li>Shows strong performance on language modeling benchmarks</li>
            </ul>
            <a href="https://arxiv.org/abs/2312.00752" class="paper-link">arXiv:2312.00752</a>
        </div>
        
        <div class="paper">
            <h3>Retrieval-Augmented Generation for Large Language Models: A Survey</h3>
            <p><strong>Authors:</strong> Lewis, P., et al.</p>
            <p><strong>Abstract:</strong> Comprehensive survey of RAG techniques for enhancing LLMs with external knowledge retrieval capabilities.</p>
            <p><strong>Categories Covered:</strong></p>
            <ul>
                <li>Dense retrieval methods</li>
                <li>Sparse retrieval techniques</li>
                <li>Hybrid approaches</li>
                <li>Evaluation metrics</li>
            </ul>
        </div>
    </div>
    
    <div class="tools-section">
        <h2>🛠️ Tools & Libraries</h2>
        <div class="tool">
            <h3>Hugging Face Transformers 4.36</h3>
            <p>Major update with support for Mamba models, improved ONNX export, and better memory optimization for large models.</p>
        </div>
    </div>
    </body>
    </html>""",
}


# Pragmatic Engineer Newsletter Sample
PRAGMATIC_ENGINEER = {
    "uid": "003",
    "subject": "The Pragmatic Engineer - Engineering Leadership in 2024",
    "sender": "gergely@pragmaticengineer.com",
    "date": "Thu, 04 Jan 2024 15:00:00 +0000",
    "content_type": "text/html",
    "body": """
    <html>
    <body>
    <div class="header">
        <h1>The Pragmatic Engineer</h1>
        <h2>Engineering Leadership in 2024</h2>
        <p>By Gergely Orosz</p>
    </div>
    
    <div class="intro">
        <p>Happy New Year! As we enter 2024, I wanted to share thoughts on the evolving landscape of engineering leadership, especially in the context of AI adoption and remote work.</p>
    </div>
    
    <div class="article-section">
        <h2>🎯 Key Trends for Engineering Leaders</h2>
        
        <div class="trend">
            <h3>1. AI-Assisted Development</h3>
            <p>GitHub Copilot and similar tools are becoming standard. Leaders need to:</p>
            <ul>
                <li>Establish guidelines for AI tool usage</li>
                <li>Retrain code review processes</li>
                <li>Balance productivity gains with code quality</li>
            </ul>
        </div>
        
        <div class="trend">
            <h3>2. Distributed Team Effectiveness</h3>
            <p>Remote work is here to stay. Successful leaders are focusing on:</p>
            <ul>
                <li>Async communication protocols</li>
                <li>Documentation-first culture</li>
                <li>Deliberate team bonding activities</li>
            </ul>
        </div>
        
        <div class="trend">
            <h3>3. Engineering Productivity Metrics</h3>
            <p>DORA metrics are becoming mainstream, but teams are adding:</p>
            <ul>
                <li>Developer experience surveys</li>
                <li>Time-to-first-commit for new hires</li>
                <li>Incident response time improvements</li>
            </ul>
        </div>
    </div>
    
    <div class="case-study">
        <h2>📊 Case Study: Scaling at Stripe</h2>
        <p>How Stripe's engineering org evolved from 50 to 500 engineers:</p>
        <ul>
            <li><strong>Microservices:</strong> Gradual extraction, not big-bang</li>
            <li><strong>Documentation:</strong> RFCs for all major decisions</li>
            <li><strong>On-call:</strong> Follow-the-sun model for global coverage</li>
        </ul>
    </div>
    </body>
    </html>""",
}


# Collection of all sample newsletters
ALL_SAMPLE_NEWSLETTERS: List[Dict[str, Any]] = [
    TLDR_NEWSLETTER,
    DEEP_LEARNING_WEEKLY,
    PRAGMATIC_ENGINEER,
]


# Expected AI summaries for testing
EXPECTED_SUMMARIES = {
    "001": {
        "title": "TLDR - Tech and Startup Updates",
        "summary": """
**Key Highlights:**

🚀 **Tech News:**
- OpenAI officially launched the GPT Store, enabling custom ChatGPT discovery and sharing across productivity, education, and lifestyle categories
- Apple Vision Pro confirmed for early February 2024 launch at $3,499, with pre-orders starting January 19th

💰 **Startup Funding:**
- AI startup Claude AI raised $50M Series B to advance constitutional AI research and compete with ChatGPT

**Impact Analysis:** The GPT Store launch represents a significant shift toward democratized AI customization, while Apple's Vision Pro pricing suggests targeting early adopters and enterprise users initially.

**Read Time:** 2 minutes
        """.strip(),
    },
    "002": {
        "title": "Deep Learning Weekly - Transformer Alternatives",
        "summary": """
**Research Highlights:**

📚 **Breakthrough Papers:**
- **Mamba Architecture:** New linear-time sequence modeling achieving O(n) complexity vs O(n²) for Transformers, excelling on 2K+ token sequences
- **RAG Survey:** Comprehensive review of retrieval-augmented generation techniques covering dense, sparse, and hybrid approaches

🛠️ **Tools Update:**
- Hugging Face Transformers 4.36 released with Mamba support, improved ONNX export, and memory optimization

**Technical Impact:** Mamba could address Transformer scalability limitations for long sequences, potentially revolutionizing applications requiring extensive context.

**Read Time:** 4 minutes
        """.strip(),
    },
    "003": {
        "title": "Engineering Leadership - 2024 Trends",
        "summary": """
**Leadership Insights:**

🎯 **Key 2024 Trends:**
1. **AI-Assisted Development:** Establishing Copilot guidelines, adapting code reviews, balancing productivity vs quality
2. **Distributed Teams:** Async protocols, documentation-first culture, deliberate team bonding
3. **Modern Metrics:** DORA metrics plus developer experience surveys and incident response tracking

📊 **Stripe Case Study:**
- Scaled 50→500 engineers via gradual microservices extraction, RFC-driven decisions, and follow-the-sun on-call

**Strategic Takeaway:** Successful 2024 engineering leaders balance AI adoption with human-centered team practices while measuring both technical and experience metrics.

**Read Time:** 3 minutes
        """.strip(),
    },
}


def get_sample_newsletter(newsletter_id: str) -> Dict[str, Any]:
    """Get a specific sample newsletter by ID."""
    newsletter_map = {
        "tldr": TLDR_NEWSLETTER,
        "deep_learning": DEEP_LEARNING_WEEKLY,
        "pragmatic": PRAGMATIC_ENGINEER,
    }
    return newsletter_map.get(newsletter_id, TLDR_NEWSLETTER)


def get_expected_summary(uid: str) -> Dict[str, str]:
    """Get expected AI summary for a newsletter UID."""
    return EXPECTED_SUMMARIES.get(
        uid,
        {
            "title": "Test Newsletter",
            "summary": "Test summary content for newsletter processing.",
        },
    )
