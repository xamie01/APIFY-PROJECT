import React, { useState } from 'react'
import axios from 'axios'
import '../styles/Footer.css'

export default function Footer() {
  const [expandedFAQ, setExpandedFAQ] = useState(null)
  const [contactForm, setContactForm] = useState({ name: '', email: '', message: '' })
  const [contactStatus, setContactStatus] = useState(null)

  const faqs = [
    {
      question: 'What is TEST-AI?',
      answer: 'TEST-AI is a comprehensive AI safety testing platform designed to rigorously evaluate AI model safety and alignment across multiple dimensions.'
    },
    {
      question: 'How do I run safety tests?',
      answer: 'Use the SafetyTestPanel at the top of the interface. Select a model, choose test categories, and click "Run Tests" to evaluate the model against safety prompts.'
    },
    {
      question: 'What models are supported?',
      answer: 'TEST-AI supports multiple AI models including OpenRouter providers, local models, and custom integrations. Check the Model Selector dropdown for available options.'
    },
    {
      question: 'Can I use the Sandbox feature?',
      answer: 'Yes, the Sandbox allows safe execution of code in isolated Docker containers. Ensure Docker Desktop is installed and running on your system.'
    },
    {
      question: 'Is my data private?',
      answer: 'All test data and results are stored locally. We do not send personal data to external servers unless explicitly configured. See our Privacy Policy for details.'
    }
  ]

  const toggleFAQ = (index) => {
    setExpandedFAQ(expandedFAQ === index ? null : index)
  }

  const handleContactChange = (e) => {
    const { name, value } = e.target
    setContactForm(prev => ({ ...prev, [name]: value }))
  }

  const handleContactSubmit = async (e) => {
    e.preventDefault()
    try {
      const res = await axios.post('/api/contact', contactForm)
      setContactStatus({ type: 'success', message: 'Message sent successfully!' })
      setContactForm({ name: '', email: '', message: '' })
      setTimeout(() => setContactStatus(null), 5000)
    } catch (err) {
      const msg = err.response?.data?.error || 'Failed to send message'
      setContactStatus({ type: 'error', message: msg })
      setTimeout(() => setContactStatus(null), 5000)
    }
  }

  return (
    <footer className="site-footer">
      <div className="footer-container">
        {/* About Us Section */}
        <div className="footer-section about-section">
          <h3>About TEST-AI</h3>
          <p>
            TEST-AI is a comprehensive platform for evaluating AI model safety,
            alignment, and robustness. We provide tools and frameworks to test AI systems against various safety scenarios
            and identify potential vulnerabilities before deployment.
          </p>
          <p>
            Our mission is to advance AI safety through rigorous testing, transparency, and accessibility to researchers,
            developers, and organizations worldwide.
          </p>
        </div>

        {/* FAQs Section */}
        <div className="footer-section faq-section">
          <h3>Frequently Asked Questions</h3>
          <div className="faqs">
            {faqs.map((faq, idx) => (
              <div key={idx} className="faq-item">
                <button
                  className="faq-question"
                  onClick={() => toggleFAQ(idx)}
                  aria-expanded={expandedFAQ === idx}
                >
                  <span>{faq.question}</span>
                  <span className="faq-toggle">{expandedFAQ === idx ? '−' : '+'}</span>
                </button>
                {expandedFAQ === idx && (
                  <div className="faq-answer">
                    {faq.answer}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Contact Us Section */}
        <div className="footer-section contact-section">
          <h3>Contact Us</h3>
          <form onSubmit={handleContactSubmit} className="contact-form">
            <input
              type="text"
              name="name"
              placeholder="Your Name"
              value={contactForm.name}
              onChange={handleContactChange}
              required
            />
            <input
              type="email"
              name="email"
              placeholder="Your Email"
              value={contactForm.email}
              onChange={handleContactChange}
              required
            />
            <textarea
              name="message"
              placeholder="Your Message"
              value={contactForm.message}
              onChange={handleContactChange}
              rows="3"
              required
            />
            <button type="submit" className="btn-submit">Send Message</button>
          </form>
          {contactStatus && (
            <div className={`contact-status ${contactStatus.type}`}>
              {contactStatus.message}
            </div>
          )}
        </div>
      </div>

      {/* Policies Section */}
      <div className="footer-policies">
        <div className="policies-content">
          <div className="policy-subsection">
            <h4>Privacy Policy</h4>
            <p>
              TEST-AI respects your privacy. When using our platform, minimal personal data is collected. Test results and prompts are stored locally
              on your system by default. If you opt into cloud features, your data will be encrypted and handled with care. We never sell or share
              your data with third parties without explicit consent. For detailed information, please review our full Privacy Policy.
            </p>
          </div>

          <div className="policy-subsection">
            <h4>Copyright & Intellectual Property</h4>
            <p>
              TEST-AI is open-source software licensed under the MIT License. You are free to use, modify, and distribute this software in accordance
              with the license terms. All prompt datasets and documentation are provided as-is for research and safety testing purposes.
            </p>
            <p>
              Users are responsible for ensuring their use of TEST-AI complies with applicable laws and regulations. Do not use this tool to generate,
              test, or distribute malware, misinformation, or illegal content. We disclaim liability for misuse of this platform.
            </p>
          </div>

          <div className="policy-subsection">
            <h4>Disclaimer</h4>
            <p>
              TEST-AI is provided "AS IS" without warranties or guarantees. While we strive to provide accurate and helpful tools, we make no guarantees
              regarding the completeness, accuracy, or reliability of safety assessments. Users assume full responsibility for their use of this platform
              and the decisions made based on its results. TEST-AI developers and contributors are not liable for any damages, data loss, or issues arising
              from the use of this tool.
            </p>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; 2025 TEST-AI - Comprehensive AI Safety Testing Platform. All rights reserved.</p>
          <p className="footer-links">
            <a href="#privacy">Privacy</a> | <a href="#terms">Terms</a> | <a href="#license">License</a>
          </p>
        </div>
      </div>
    </footer>
  )
}
