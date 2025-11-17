import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronRightIcon, PlusIcon, MinusIcon, SearchIcon } from 'lucide-react';
import { categories, faqItems } from '../data/faq';

export const FAQ = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [openQuestions, setOpenQuestions] = useState([]);

  // Toggle question open/closed
  const toggleQuestion = (id) => {
    if (openQuestions.includes(id)) {
      setOpenQuestions(openQuestions.filter((qId) => qId !== id));
    } else {
      setOpenQuestions([...openQuestions, id]);
    }
  };

  // Filter questions based on search term and active category
  const filteredQuestions = faqItems.filter((item) => {
    const matchesSearch =
      item.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.answer.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = activeCategory === 'all' || item.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="container mx-auto px-4 py-8 text-copy">
      {/* Breadcrumb */}
      <nav className="flex mb-6 text-sm">
        <Link to="/" className="text-copy-lighter hover:text-primary">
          Home
        </Link>
        <ChevronRightIcon size={16} className="mx-2" />
        <span className="text-copy">Frequently Asked Questions</span>
      </nav>

      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-3xl md:text-4xl font-bold text-copy mb-4">Frequently Asked Questions</h1>
          <p className="text-copy-light max-w-2xl mx-auto">
            Find answers to common questions about our products, shipping, returns, and more. Can't find what you're
            looking for? Contact our support team.
          </p>
        </div>

        {/* Search bar */}
        <div className="mb-8">
          <div className="relative">
            <input
              type="text"
              placeholder="Search for questions..."
              className="w-full px-4 py-3 pl-12 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-transparent"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <SearchIcon size={20} className="absolute left-4 top-1/2 transform -translate-y-1/2 text-copy-lighter" />
          </div>
        </div>

        {/* Categories */}
        <div className="mb-8 overflow-x-auto">
          <div className="flex space-x-2 min-w-max">
            {categories.map((category) => (
              <button
                key={category.id}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap ${
                  activeCategory === category.id
                    ? 'bg-primary text-white'
                    : 'bg-surface text-copy hover:bg-border'
                }`}
                onClick={() => setActiveCategory(category.id)}>
                {category.name}
              </button>
            ))}
          </div>
        </div>

        {/* FAQ items */}
        <div className="space-y-4">
          {filteredQuestions.length > 0 ? (
            filteredQuestions.map((item) => (
              <div key={item.id} className="bg-surface rounded-lg shadow-sm border border-border-light overflow-hidden">
                <button
                  className="flex justify-between items-center w-full p-6 text-left"
                  onClick={() => toggleQuestion(item.id)}>
                  <h3 className="font-medium text-copy text-lg">{item.question}</h3>
                  {openQuestions.includes(item.id) ? (
                    <MinusIcon size={20} className="text-primary flex-shrink-0" />
                  ) : (
                    <PlusIcon size={20} className="text-primary flex-shrink-0" />
                  )}
                </button>
                {openQuestions.includes(item.id) && (
                  <div className="px-6 pb-6">
                    <div className="pt-2 border-t border-border-light">
                      <p className="text-copy-light mt-4">{item.answer}</p>
                    </div>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="text-center py-12 bg-surface rounded-lg shadow-sm">
              <div className="mx-auto w-16 h-16 bg-background rounded-full flex items-center justify-center mb-4">
                <SearchIcon size={24} className="text-copy-lighter" />
              </div>
              <h3 className="text-lg font-medium text-copy mb-2">No results found</h3>
              <p className="text-copy-light">
                Try adjusting your search or filter to find what you're looking for
              </p>
            </div>
          )}
        </div>

        {/* Contact section */}
        <div className="mt-16 bg-primary/10 rounded-lg p-6 md:p-8 text-center">
          <h2 className="text-xl font-bold text-copy mb-4">Still have questions?</h2>
          <p className="text-copy-light mb-6 max-w-md mx-auto">
            If you couldn't find the answer you were looking for, our support team is here to help.
          </p>
          <Link
            to="/contact"
            className="inline-block bg-primary hover:bg-primary-dark text-white px-6 py-3 rounded-md transition-colors">
            Contact Support
          </Link>
        </div>
      </div>
    </div>
  );
};