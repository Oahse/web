/**
 * Dedicated Support Page
 * Comprehensive customer support page with multiple contact options
 */

import React from 'react';
import { useSearchParams } from 'react-router-dom';
import CustomerSupport from '../components/support/CustomerSupport';
import { MessageCircle, Phone, Mail, Clock, HelpCircle } from 'lucide-react';

const Support: React.FC = () => {
  const [searchParams] = useSearchParams();
  
  // Get context from URL parameters
  const orderNumber = searchParams.get('order') || undefined;
  const productId = searchParams.get('product') || undefined;
  const issueType = (searchParams.get('type') as 'order' | 'payment' | 'product' | 'account' | 'general') || 'general';

  const faqItems = [
    {
      question: "How do I track my order?",
      answer: "You can track your order by going to 'My Orders' in your account or using the tracking link sent to your email."
    },
    {
      question: "What is your return policy?",
      answer: "We offer a 30-day return policy for most items. Items must be in original condition with tags attached."
    },
    {
      question: "How long does shipping take?",
      answer: "Standard shipping takes 3-5 business days. Express shipping takes 1-2 business days."
    },
    {
      question: "How do I cancel my order?",
      answer: "You can cancel your order within 1 hour of placing it by going to 'My Orders' and clicking 'Cancel Order'."
    },
    {
      question: "What payment methods do you accept?",
      answer: "We accept all major credit cards, PayPal, Apple Pay, and Google Pay."
    }
  ];

  const contactMethods = [
    {
      icon: <MessageCircle className="w-8 h-8 text-green-600" />,
      title: "WhatsApp Support",
      description: "Get instant help via WhatsApp",
      availability: "24/7",
      responseTime: "< 2 minutes",
      action: "Chat Now",
      primary: true
    },
    {
      icon: <Phone className="w-8 h-8 text-blue-600" />,
      title: "Phone Support",
      description: "Speak directly with our team",
      availability: "9 AM - 9 PM EST",
      responseTime: "Immediate",
      action: "Call Now",
      primary: false
    },
    {
      icon: <Mail className="w-8 h-8 text-purple-600" />,
      title: "Email Support",
      description: "Send us a detailed message",
      availability: "24/7",
      responseTime: "< 4 hours",
      action: "Send Email",
      primary: false
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            How Can We Help You? 🤝
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Our customer support team is here to help you 24/7. Get instant assistance via WhatsApp 
            or choose from our other support options below.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Support Widget */}
          <div className="lg:col-span-2">
            <CustomerSupport
              orderNumber={orderNumber}
              productId={productId}
              issueType={issueType}
            />
          </div>

          {/* Contact Methods */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                Contact Methods
              </h3>
              
              <div className="space-y-4">
                {contactMethods.map((method, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg border-2 ${
                      method.primary 
                        ? 'border-green-500 bg-green-50' 
                        : 'border-gray-200 hover:border-gray-300'
                    } transition-colors`}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0">
                        {method.icon}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 mb-1">
                          {method.title}
                        </h4>
                        <p className="text-sm text-gray-600 mb-2">
                          {method.description}
                        </p>
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <span>{method.availability}</span>
                          <span className="font-medium text-green-600">
                            {method.responseTime}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Support Hours */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                <Clock className="w-5 h-5 mr-2" />
                Support Hours
              </h3>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">WhatsApp Support:</span>
                  <span className="font-medium text-green-600">24/7</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Phone Support:</span>
                  <span className="font-medium">9 AM - 9 PM EST</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Email Support:</span>
                  <span className="font-medium">24/7</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mt-12">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
              <HelpCircle className="w-6 h-6 mr-2" />
              Frequently Asked Questions
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {faqItems.map((item, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-2">
                    {item.question}
                  </h3>
                  <p className="text-gray-600 text-sm">
                    {item.answer}
                  </p>
                </div>
              ))}
            </div>
            
            <div className="mt-6 text-center">
              <p className="text-gray-600 mb-4">
                Can't find what you're looking for?
              </p>
              <button className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors">
                Contact Support
              </button>
            </div>
          </div>
        </div>

        {/* Emergency Support */}
        <div className="mt-8 bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm">!</span>
              </div>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-red-800">
                Emergency Support
              </h3>
              <p className="text-red-700">
                For urgent issues like payment problems or order emergencies, 
                use our WhatsApp urgent support for immediate assistance.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export { Support };
export default Support;