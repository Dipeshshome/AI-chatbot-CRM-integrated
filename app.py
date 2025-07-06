from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import re
from datetime import datetime, timedelta
import sqlite3
import os
from typing import Dict, List, Optional
import logging
import random
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
class Config:
    # CRM API Configuration (using HubSpot as example)
    HUBSPOT_API_KEY = os.getenv('HUBSPOT_API_KEY')
    HUBSPOT_BASE_URL = 'https://api.hubapi.com'
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_BASE_URL = 'https://api.openai.com/v1'
    
    # Database
    DATABASE_PATH = 'chatbot.db'

# Dummy Data Knowledge Base
class KnowledgeBase:
    def __init__(self):
        self.company_info = {
            "name": "TechFlow Solutions",
            "description": "Leading provider of cloud-based CRM and business automation software",
            "founded": "2018",
            "employees": "250+",
            "headquarters": "San Francisco, CA",
            "offices": ["San Francisco", "Austin", "New York", "London"],
            "phone": "1-800-TECHFLOW (1-800-832-4356)",
            "email": "info@techflowsolutions.com",
            "website": "www.techflowsolutions.com"
        }
        
        self.products = {
            "crm_professional": {
                "name": "CRM Professional",
                "description": "Complete customer relationship management solution for growing businesses",
                "features": ["Contact Management", "Sales Pipeline", "Email Integration", "Reporting", "Mobile App"],
                "price": "$49/user/month",
                "target": "Small to medium businesses (5-50 employees)",
                "trial": "14-day free trial"
            },
            "crm_enterprise": {
                "name": "CRM Enterprise", 
                "description": "Advanced CRM with custom integrations and enterprise-grade security",
                "features": ["All Professional features", "Custom Integrations", "Advanced Analytics", "SSO", "Dedicated Support"],
                "price": "Custom pricing starting at $99/user/month",
                "target": "Large businesses (50+ employees)",
                "trial": "30-day free trial"
            },
            "automation_suite": {
                "name": "Business Automation Suite",
                "description": "Complete workflow automation platform",
                "features": ["Process Automation", "Document Management", "Approval Workflows", "Integration Hub"],
                "price": "$29/user/month",
                "target": "All business sizes",
                "trial": "21-day free trial"
            }
        }
        
        self.services = {
            "implementation": {
                "name": "Implementation Services",
                "description": "Professional setup and configuration of your CRM system",
                "duration": "2-8 weeks depending on complexity",
                "price": "Starting at $2,500"
            },
            "training": {
                "name": "Training & Onboarding",
                "description": "Comprehensive training for your team",
                "formats": ["Live virtual sessions", "On-site training", "Self-paced online"],
                "price": "$150/hour or $1,200/day"
            },
            "support": {
                "name": "Premium Support",
                "description": "24/7 technical support with dedicated account manager",
                "response_time": "< 2 hours for critical issues",
                "price": "$500/month"
            }
        }
        
        self.case_studies = {
            "retail": {
                "company": "RetailMax Inc.",
                "industry": "Retail",
                "size": "150 employees",
                "challenge": "Managing customer data across 25 store locations",
                "solution": "CRM Enterprise with custom POS integration",
                "results": "40% increase in customer retention, 25% boost in sales"
            },
            "manufacturing": {
                "company": "Industrial Parts Co.",
                "industry": "Manufacturing", 
                "size": "300 employees",
                "challenge": "Complex B2B sales cycles and lead tracking",
                "solution": "CRM Professional + Business Automation Suite",
                "results": "60% faster sales cycle, 35% more qualified leads"
            },
            "healthcare": {
                "company": "MedTech Solutions",
                "industry": "Healthcare Technology",
                "size": "75 employees", 
                "challenge": "HIPAA compliance and patient data management",
                "solution": "CRM Enterprise with healthcare compliance package",
                "results": "100% HIPAA compliance, 50% reduction in admin time"
            }
        }
        
        self.faqs = {
            "pricing": {
                "question": "What are your pricing plans?",
                "answer": "We offer three main plans: CRM Professional at $49/user/month, CRM Enterprise with custom pricing starting at $99/user/month, and Business Automation Suite at $29/user/month. All plans include free trials."
            },
            "trial": {
                "question": "Do you offer free trials?",
                "answer": "Yes! We offer 14-day free trials for CRM Professional, 30-day trials for CRM Enterprise, and 21-day trials for Business Automation Suite. No credit card required to start."
            },
            "integration": {
                "question": "What integrations do you support?",
                "answer": "We integrate with 200+ popular business tools including Salesforce, HubSpot, Slack, Microsoft Office 365, Google Workspace, QuickBooks, Shopify, and many more."
            },
            "security": {
                "question": "How secure is your platform?",
                "answer": "We're SOC 2 Type II certified with enterprise-grade encryption, regular security audits, and comply with GDPR, HIPAA, and other industry standards."
            },
            "support": {
                "question": "What support do you provide?",
                "answer": "We offer 24/7 email support for all plans, live chat during business hours, phone support for Enterprise customers, and premium 24/7 phone support as an add-on."
            }
        }
        
        self.testimonials = [
            {
                "customer": "Sarah Johnson",
                "company": "GrowthTech Inc.",
                "role": "VP of Sales",
                "quote": "TechFlow's CRM transformed our sales process. We've seen a 45% increase in conversion rates since implementation."
            },
            {
                "customer": "Mike Chen",
                "company": "DataDriven LLC", 
                "role": "CEO",
                "quote": "The automation features saved us 20 hours per week. Best investment we've made for our business operations."
            },
            {
                "customer": "Lisa Rodriguez",
                "company": "ServiceFirst Corp",
                "role": "Customer Success Manager",
                "quote": "Customer support is outstanding. They helped us customize the system perfectly for our unique needs."
            }
        ]
        
        # Sample existing customers for realistic responses
        self.existing_customers = {
            "john@growthco.com": {
                "name": "John Smith",
                "company": "Growth Co",
                "plan": "CRM Professional",
                "since": "2023-06-15",
                "status": "Active"
            },
            "sarah@techstartup.com": {
                "name": "Sarah Davis", 
                "company": "Tech Startup Inc",
                "plan": "CRM Enterprise",
                "since": "2023-03-22",
                "status": "Active"
            },
            "mike@retailplus.com": {
                "name": "Mike Johnson",
                "company": "Retail Plus",
                "plan": "Business Automation Suite",
                "since": "2023-09-10", 
                "status": "Trial"
            }
        }

kb = KnowledgeBase()

class DatabaseManager:
    def __init__(self):
        self.init_database()
        self.populate_dummy_data()
    
    def init_database(self):
        """Initialize SQLite database for conversation history"""
        try:
            conn = sqlite3.connect(Config.DATABASE_PATH)
            cursor = conn.cursor()
            
            # Conversations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    intent TEXT,
                    crm_contact_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Contacts cache table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contacts_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    crm_contact_id TEXT UNIQUE NOT NULL,
                    email TEXT,
                    name TEXT,
                    phone TEXT,
                    company TEXT,
                    plan TEXT,
                    status TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def populate_dummy_data(self):
        """Populate database with dummy customer data"""
        try:
            conn = sqlite3.connect(Config.DATABASE_PATH)
            cursor = conn.cursor()
            
            # Check if data already exists
            cursor.execute("SELECT COUNT(*) FROM contacts_cache")
            count = cursor.fetchone()[0]
            
            if count == 0:  # Only insert if table is empty
                dummy_contacts = [
                    ("john@growthco.com", "john_123", "John Smith", "+1-555-0123", "Growth Co", "CRM Professional", "Active"),
                    ("sarah@techstartup.com", "sarah_456", "Sarah Davis", "+1-555-0124", "Tech Startup Inc", "CRM Enterprise", "Active"),
                    ("mike@retailplus.com", "mike_789", "Mike Johnson", "+1-555-0125", "Retail Plus", "Business Automation Suite", "Trial"),
                    ("lisa@designstudio.com", "lisa_101", "Lisa Chen", "+1-555-0126", "Design Studio Pro", "CRM Professional", "Active"),
                    ("alex@consulting.com", "alex_202", "Alex Thompson", "+1-555-0127", "Transform Consulting", "CRM Enterprise", "Active")
                ]
                
                for email, crm_id, name, phone, company, plan, status in dummy_contacts:
                    cursor.execute('''
                        INSERT OR IGNORE INTO contacts_cache 
                        (email, crm_contact_id, name, phone, company, plan, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (email, crm_id, name, phone, company, plan, status))
                
                conn.commit()
                logger.info("Dummy data populated successfully")
            
            conn.close()
        except Exception as e:
            logger.error(f"Error populating dummy data: {e}")
    
    def save_conversation(self, session_id: str, user_message: str, bot_response: str, 
                         intent: str = None, crm_contact_id: str = None):
        """Save conversation to database"""
        try:
            conn = sqlite3.connect(Config.DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO conversations (session_id, user_message, bot_response, intent, crm_contact_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, user_message, bot_response, intent, crm_contact_id))
            
            conn.commit()
            conn.close()
            logger.info(f"Conversation saved for session: {session_id}")
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
    
    def get_conversation_history(self, session_id: str, limit: int = 5) -> List[Dict]:
        """Get recent conversation history"""
        try:
            conn = sqlite3.connect(Config.DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_message, bot_response, timestamp 
                FROM conversations 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (session_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [{'user': row[0], 'bot': row[1], 'timestamp': row[2]} for row in reversed(rows)]
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def get_contact_by_email(self, email: str) -> Optional[Dict]:
        """Get contact from local database"""
        try:
            conn = sqlite3.connect(Config.DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT crm_contact_id, email, name, phone, company, plan, status
                FROM contacts_cache 
                WHERE email = ?
            ''', (email,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'email': row[1], 
                    'name': row[2],
                    'phone': row[3],
                    'company': row[4],
                    'plan': row[5],
                    'status': row[6]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting contact: {e}")
            return None

class CRMIntegration:
    def __init__(self, db_manager):
        self.api_key = Config.HUBSPOT_API_KEY
        self.base_url = Config.HUBSPOT_BASE_URL
        self.db = db_manager
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def search_contact(self, email: str = None, phone: str = None) -> Optional[Dict]:
        """Search for contact in CRM"""
        try:
            # First check local database
            if email:
                contact = self.db.get_contact_by_email(email)
                if contact:
                    return contact
            
            # Return mock data for demo
            return self._mock_contact_search(email, phone)
            
        except Exception as e:
            logger.error(f"Error searching contact: {e}")
            return None
    
    def _mock_contact_search(self, email: str = None, phone: str = None) -> Optional[Dict]:
        """Mock contact search with realistic data"""
        if email and email in kb.existing_customers:
            customer = kb.existing_customers[email]
            return {
                'id': f'contact_{email.split("@")[0]}',
                'email': email,
                'name': customer['name'],
                'phone': phone or '+1-555-0123',
                'company': customer['company'],
                'plan': customer['plan'],
                'status': customer['status']
            }
        return None
    
    def create_contact(self, email: str, name: str = None, phone: str = None, company: str = None) -> Optional[Dict]:
        """Create new contact in CRM"""
        try:
            # Create realistic mock contact
            contact_id = f'new_contact_{datetime.now().timestamp()}'
            contact = {
                'id': contact_id,
                'email': email,
                'name': name or 'New Contact',
                'phone': phone,
                'company': company,
                'plan': 'Trial',
                'status': 'New Lead'
            }
            
            # Save to local database
            conn = sqlite3.connect(Config.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO contacts_cache 
                (crm_contact_id, email, name, phone, company, plan, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (contact_id, email, name, phone, company, 'Trial', 'New Lead'))
            conn.commit()
            conn.close()
            
            return contact
            
        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            return None

class SmartResponseGenerator:
    def __init__(self):
        self.kb = kb
    
    def generate_contextual_response(self, message: str, intent: str, context: Dict = None) -> str:
        """Generate intelligent responses based on intent and context"""
        
        message_lower = message.lower()
        
        # Company information queries
        if any(word in message_lower for word in ['company', 'about', 'who are you', 'business']):
            return f"I represent {self.kb.company_info['name']}, a {self.kb.company_info['description']}. We were founded in {self.kb.company_info['founded']} and now serve thousands of businesses worldwide with our cloud-based solutions. We have {self.kb.company_info['employees']} employees across offices in {', '.join(self.kb.company_info['offices'])}."
        
        # Product information queries
        if intent == 'product_inquiry':
            if any(word in message_lower for word in ['price', 'cost', 'pricing', 'plans']):
                return self._get_pricing_info()
            elif any(word in message_lower for word in ['features', 'functionality', 'capabilities']):
                return self._get_features_info()
            elif any(word in message_lower for word in ['enterprise', 'large', 'big company']):
                return self._get_enterprise_info()
            elif any(word in message_lower for word in ['small', 'startup', 'growing']):
                return self._get_small_business_info()
            else:
                return self._get_general_product_info()
        
        # Support queries
        if intent == 'support':
            if context and context.get('contact') and context['contact'].get('plan'):
                plan = context['contact']['plan']
                return f"I can help you with support for your {plan} account. Our support team provides 24/7 email support, and since you're on {plan}, you also have access to priority support. What specific issue can I help you troubleshoot?"
            else:
                return "I'm here to help with any technical issues. Our support team provides 24/7 email support for all customers, with priority phone support for Enterprise customers. What specific problem are you experiencing?"
        
        # Trial and demo requests
        if any(word in message_lower for word in ['trial', 'demo', 'test', 'try']):
            return self._get_trial_info()
        
        # Integration queries
        if any(word in message_lower for word in ['integrate', 'connect', 'api', 'sync']):
            return "We integrate with 200+ popular business tools including Salesforce, HubSpot, Slack, Microsoft Office 365, Google Workspace, QuickBooks, and Shopify. Our Integration Hub makes it easy to connect your existing tools. What specific integrations are you looking for?"
        
        # Security queries
        if any(word in message_lower for word in ['security', 'safe', 'compliance', 'gdpr', 'hipaa']):
            return "Security is our top priority. We're SOC 2 Type II certified with enterprise-grade encryption, regular security audits, and full compliance with GDPR, HIPAA, and other industry standards. All data is encrypted in transit and at rest."
        
        # Case studies and success stories
        if any(word in message_lower for word in ['case study', 'success', 'results', 'roi']):
            return self._get_case_study()
        
        # Contact information
        if intent == 'contact_info':
            return f"""Here's how you can reach us:

📞 Phone: {self.kb.company_info['phone']}

📧 Email: {self.kb.company_info['email']}

🌐 Website: {self.kb.company_info['website']}

🏢 Headquarters: {self.kb.company_info['headquarters']}

Our sales team is available Monday-Friday, 9 AM - 6 PM EST. 

Would you like me to have someone contact you directly?"""
        
        # Lead qualification responses
        if intent == 'lead_qualification':
            if context and context.get('contact'):
                contact = context['contact']
                return f"Thank you for your interest, {contact.get('name', 'there')}! I've captured your information and our sales team will reach out within 2 hours. Based on your needs, I'd recommend starting with a personalized demo. What's the best time to reach you for a 30-minute product walkthrough?"
            else:
                return "I'd love to learn more about your business needs! Could you tell me about your company size, current challenges, and what you're hoping to achieve with a CRM solution?"
        
        # Fallback responses based on intent
        return self._get_fallback_response(intent, context)
    
    def _get_pricing_info(self) -> str:
        return f"""Here are our current pricing plans:

💼 CRM Professional - ${self.kb.products['crm_professional']['price']}
Perfect for {self.kb.products['crm_professional']['target']}

Key Features:
• Contact Management
• Sales Pipeline  
• Email Integration
• Reporting
• Mobile App
• {self.kb.products['crm_professional']['trial']}

🏢 CRM Enterprise - {self.kb.products['crm_enterprise']['price']}
Designed for {self.kb.products['crm_enterprise']['target']}

Key Features:
• All Professional features
• Custom Integrations
• Advanced Analytics
• Single Sign-On (SSO)
• Dedicated Support
• {self.kb.products['crm_enterprise']['trial']}

⚙️ Business Automation Suite - ${self.kb.products['automation_suite']['price']}

Key Features:
• Process Automation
• Document Management
• Approval Workflows
• Integration Hub
• {self.kb.products['automation_suite']['trial']}

All plans include free onboarding and email support. 

Would you like to start a free trial?"""
    
    def _get_features_info(self) -> str:
        return """Our platform includes comprehensive features to streamline your business:

🎯 Core CRM Features:
• Contact & Lead Management
• Sales Pipeline Tracking
• Email Integration & Templates
• Task & Activity Management
• Reporting & Analytics

🔧 Advanced Features:
• Workflow Automation
• Custom Fields & Forms
• API Integration Hub
• Mobile Apps (iOS & Android)
• Advanced Security Controls

🎓 Training & Support:
• Live onboarding sessions
• Video training library
• 24/7 email support
• Phone support (Enterprise)

Which features are most important for your business needs?"""
    
    def _get_enterprise_info(self) -> str:
        return f"""Our CRM Enterprise solution is perfect for large organizations:

🏢 Enterprise Features:
• Unlimited custom integrations
• Advanced analytics & reporting
• Single Sign-On (SSO)
• Dedicated account manager
• Priority 24/7 phone support
• Custom training programs

📊 Success Story:
{self.kb.case_studies['manufacturing']['company']} ({self.kb.case_studies['manufacturing']['size']}) saw {self.kb.case_studies['manufacturing']['results']} after implementing our Enterprise solution.

💰 Pricing: Custom quotes starting at $99/user/month

🆓 Trial: 30-day free trial with dedicated setup support

Would you like to schedule an enterprise demo with our solutions architect?"""
    
    def _get_small_business_info(self) -> str:
        return f"""Perfect! Our CRM Professional is designed specifically for growing businesses:

🚀 Ideal for Small/Medium Businesses:
• Easy setup - get started in under an hour
• Affordable at just ${self.kb.products['crm_professional']['price']}
• Scales with your business growth
• No technical expertise required

✨ What's Included:
• Contact Management
• Sales Pipeline
• Email Integration
• Reporting
• Mobile App

📈 Success Story:
{self.kb.case_studies['retail']['company']} saw {self.kb.case_studies['retail']['results']} within 6 months of implementation.

🎁 Special Offer: {self.kb.products['crm_professional']['trial']} - no credit card required!

Ready to transform your customer relationships?"""
    
    def _get_general_product_info(self) -> str:
        return f"""Welcome to {self.kb.company_info['name']}! We offer comprehensive business solutions:

🎯 Our Products:

CRM Professional - Complete customer relationship management (${self.kb.products['crm_professional']['price']})

CRM Enterprise - Advanced features for larger teams (Custom pricing)

Business Automation Suite - Workflow automation tools (${self.kb.products['automation_suite']['price']})

🌟 Why Choose Us:
• Trusted by thousands of businesses worldwide
• 99.9% uptime guarantee
• Award-winning customer support
• ROI typically seen within 90 days

🎁 Free Trials Available:
All our solutions come with free trials ranging from 14-30 days.

What type of business challenges are you looking to solve?"""
    
    def _get_trial_info(self) -> str:
        return f"""Great news! We offer generous free trials for all our products:

🆓 Free Trial Options:

CRM Professional: {self.kb.products['crm_professional']['trial']}

CRM Enterprise: {self.kb.products['crm_enterprise']['trial']}

Business Automation Suite: {self.kb.products['automation_suite']['trial']}

✅ What's Included:
• Full access to all features
• Free setup and onboarding
• Email support throughout trial
• No credit card required
• Easy upgrade anytime

🎯 Perfect for:
• Testing our platform with your real data
• Training your team
• Evaluating ROI before commitment

Ready to start your free trial? I can set that up for you right now!"""
    
    def _get_case_study(self) -> str:
        cases = list(self.kb.case_studies.values())
        case = random.choice(cases)
        return f"""Here's a recent success story:

🏢 {case['company']} ({case['industry']})

📊 Company Size: {case['size']}

🎯 Challenge: {case['challenge']}

💡 Solution: {case['solution']}

📈 Results: {case['results']}

We have many more success stories across different industries. Would you like to see case studies specific to your industry?"""
    
    def _get_fallback_response(self, intent: str, context: Dict = None) -> str:
        responses = {
            'greeting': f"Hello! Welcome to {self.kb.company_info['name']}. I'm your AI assistant and I'm here to help you discover how our CRM and automation solutions can transform your business. What can I help you with today?",
            'general': f"Thank you for your interest in {self.kb.company_info['name']}! We're the leading provider of cloud-based CRM solutions, trusted by thousands of businesses worldwide. Whether you need customer management, sales automation, or business process optimization, we have the perfect solution. How can I help you today?"
        }
        
        if context and context.get('contact'):
            contact = context['contact']
            return f"Hi {contact.get('name', 'there')}! I see you're {'already a valued customer' if contact.get('status') == 'Active' else 'interested in our solutions'}. How can I assist you today?"
        
        return responses.get(intent, responses['general'])

class IntentClassifier:
    def __init__(self):
        self.intents = {
            'greeting': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening'],
            'contact_info': ['contact', 'phone', 'address', 'reach', 'get in touch', 'call', 'email'],
            'product_inquiry': ['product', 'service', 'price', 'cost', 'buy', 'purchase', 'pricing', 'plan', 'features'],
            'support': ['help', 'support', 'issue', 'problem', 'bug', 'error', 'trouble', 'not working'],
            'lead_qualification': ['interested', 'quote', 'demo', 'trial', 'meeting', 'schedule', 'sales'],
            'order_status': ['order', 'status', 'delivery', 'shipped', 'tracking', 'when will']
        }
    
    def classify_intent(self, message: str) -> str:
        """Enhanced intent classification"""
        message_lower = message.lower()
        
        # Check for multiple intents and prioritize
        detected_intents = []
        for intent, keywords in self.intents.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_intents.append(intent)
        
        # Prioritize certain intents
        if 'support' in detected_intents:
            return 'support'
        elif 'lead_qualification' in detected_intents:
            return 'lead_qualification'
        elif 'product_inquiry' in detected_intents:
            return 'product_inquiry'
        elif detected_intents:
            return detected_intents[0]
        
        return 'general'

class ChatbotEngine:
    def __init__(self):
        self.db = DatabaseManager()
        self.crm = CRMIntegration(self.db)
        self.response_generator = SmartResponseGenerator()
        self.intent_classifier = IntentClassifier()
    
    def extract_email(self, message: str) -> Optional[str]:
        """Extract email from message"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, message)
        return emails[0] if emails else None
    
    def extract_phone(self, message: str) -> Optional[str]:
        """Extract phone number from message"""
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, message)
        return phones[0] if phones else None
    
    def process_message(self, message: str, session_id: str) -> Dict:
        """Main message processing function with enhanced intelligence"""
        try:
            # Classify intent
            intent = self.intent_classifier.classify_intent(message)
            
            # Extract contact information
            email = self.extract_email(message)
            phone = self.extract_phone(message)
            
            # Initialize context
            context = {
                'intent': intent,
                'email': email,
                'phone': phone,
                'timestamp': datetime.now().isoformat()
            }
            
            # CRM operations based on intent
            contact = None
            crm_contact_id = None
            
            if email or phone:
                # Search for existing contact
                contact = self.crm.search_contact(email=email, phone=phone)
                if contact:
                    crm_contact_id = contact['id']
                    context['contact'] = contact
                elif email:
                    # Create new contact if email provided
                    contact = self.crm.create_contact(email=email, phone=phone)
                    if contact:
                        crm_contact_id = contact['id']
                        context['contact'] = contact
            
            # Generate intelligent response
            response = self.response_generator.generate_contextual_response(message, intent, context)
            
            # Save conversation
            self.db.save_conversation(
                session_id=session_id,
                user_message=message,
                bot_response=response,
                intent=intent,
                crm_contact_id=crm_contact_id
            )
            
            return {
                'response': response,
                'intent': intent,
                'context': context,
                'contact': contact
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                'response': f"I apologize, but I encountered an error. Please try rephrasing your question. If you need immediate assistance, you can reach our support team at {kb.company_info['phone']}.",
                'intent': 'error',
                'context': {},
                'contact': None
            }

# Initialize chatbot engine
chatbot = ChatbotEngine()

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        data = request.json
        message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Process message
        result = chatbot.process_message(message, session_id)
        
        return jsonify({
            'response': result['response'],
            'intent': result['intent'],
            'contact': result.get('contact'),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/history/<session_id>', methods=['GET'])
def get_history(session_id):
    """Get conversation history"""
    try:
        history = chatbot.db.get_conversation_history(session_id)
        return jsonify({'history': history})
    except Exception as e:
        logger.error(f"History endpoint error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if os.path.exists(Config.DATABASE_PATH) else 'not found',
        'company': kb.company_info['name']
    })

@app.route('/company-info', methods=['GET'])
def get_company_info():
    """Get company information endpoint"""
    return jsonify({
        'company': kb.company_info,
        'products': kb.products,
        'services': kb.services
    })

if __name__ == '__main__':
    logger.info(f"Starting {kb.company_info['name']} AI CRM Chatbot Server on port 8083")
    app.run(debug=True, host='0.0.0.0', port=8083)