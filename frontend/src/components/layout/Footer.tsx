import { Link } from 'react-router-dom';
import { MapPinIcon, MailIcon, PhoneIcon, ArrowRightIcon, FacebookIcon, TwitterIcon, InstagramIcon, YoutubeIcon, LinkedinIcon } from 'lucide-react';
import { SOCIAL_MEDIA_LINKS } from '../../utils/social-media-config';

export const Footer = () => {
  // Categories for quick links - matching backend API query parameters
  const categories = [
    { name: 'Cereal Crops', path: '/products?category=Cereal Crops' },
    { name: 'Legumes', path: '/products?category=Legumes' },
    { name: 'Fruits & Vegetables', path: '/products?category=Fruits and Vegetables' },
    { name: 'Spices and Herbs', path: '/products?category=Spices and Herbs' },
    { name: 'Nuts & Beverages', path: '/products?category=Nuts, Flowers and Beverages' },
  ];

  // Help links
  const helpLinks = [
    { name: 'About Us', path: '/about' },
    { name: 'Contact', path: '/contact' },
    { name: 'FAQ', path: '/faq' },
    { name: 'Terms & Conditions', path: '/terms' },
    { name: 'Privacy Policy', path: '/privacy' },
  ];

  // Account links
  const accountLinks = [
    { name: 'My Account', path: '/account' },
    { name: 'My Orders', path: '/account/orders' },
    { name: 'Wishlist', path: '/account/wishlist' },
    { name: 'Track Order', path: '/account/track-order' },
  ];

  return (
    <footer className="bg-surface pt-12 pb-16 md:pb-10 border-t border-border-light mt-12 text-copy">
      <div className="container mx-auto px-4 max-w-[1400px]">
        {/* Subscriptions */}
        <div className="bg-background rounded-lg p-6 md:p-10 mb-12">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div className="mb-6 md:mb-0 md:mr-8">
              <h3 className="text-2xl font-bold text-main mb-3">Manage Your Subscriptions</h3>
              <p className="text-copy-light">Explore, set up, and manage your recurring orders and subscriptions.</p>
            </div>
            <div className="flex-shrink-0 w-full md:w-auto">
              <Link
                to="/account/subscriptions"
                className="bg-primary text-copy-inverse px-6 py-3 rounded-md hover:bg-primary-dark transition-colors flex items-center justify-center whitespace-nowrap"
              >
                Go to Subscriptions
                <ArrowRightIcon size={16} className="ml-2" />
              </Link>
            </div>
          </div>
        </div>

        {/* Main Footer */}
        <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-6 gap-6 md:gap-8 lg:gap-12">
          {/* Company Info */}
          <div className="col-span-2 md:col-span-2 lg:col-span-2">
            <Link to="/" className="inline-block mb-4">
              <div className="flex items-center">
                <img src="/banwee_logo_text_green.png" alt="Banwee" className="h-6" />
              </div>
            </Link>
            <p className="text-copy-light mb-6 max-w-md">
              Banwee brings you the finest organic products from Africa, ethically sourced and sustainably
              produced.
            </p>
            <div className="space-y-4">
              <div className="flex items-start">
                <MapPinIcon size={20} className="text-primary flex-shrink-0 mr-3 mt-1" />
                <p className="text-copy-light">
                  1234 Fashion Street, Suite 567, New York, NY 10001
                </p>
              </div>
              <div className="flex items-center">
                <MailIcon size={20} className="text-primary flex-shrink-0 mr-3" />
                <a href="mailto:info@banwee.com" className="text-copy-light hover:text-primary">
                  info@banwee.com
                </a>
              </div>
              <div className="flex items-center">
                <PhoneIcon size={20} className="text-primary flex-shrink-0 mr-3" />
                <a href="tel:+12125551234" className="text-copy-light hover:text-primary">
                  (212) 555-1234
                </a>
              </div>
              <Link to="/contact" className="inline-flex items-center text-primary hover:underline">
                Get direction
                <ArrowRightIcon size={16} className="ml-2" />
              </Link>
            </div>
          </div>

          {/* Categories */}
          <div>
            <h5 className="text-lg font-semibold text-main mb-5">Shop Categories</h5>
            <ul className="space-y-3">
              {categories.map((category, index) => (
                <li key={index}>
                  <Link to={category.path} className="text-copy-light hover:text-primary">
                    {category.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Help */}
          <div>
            <h5 className="text-lg font-semibold text-main mb-5">Help</h5>
            <ul className="space-y-3">
              {helpLinks.map((link, index) => (
                <li key={index}>
                  <Link to={link.path} className="text-copy-light hover:text-primary">
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Account */}
          <div>
            <h5 className="text-lg font-semibold text-main mb-5">My Account</h5>
            <ul className="space-y-3">
              {accountLinks.map((link, index) => (
                <li key={index}>
                  <Link to={link.path} className="text-copy-light hover:text-primary">
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Mobile App */}
          <div>
            <h5 className="text-lg font-semibold text-main mb-5">Get Our App</h5>
            <div className="space-y-3">
              <a
                href="#"
                className="block w-full max-w-[140px] hover:opacity-80 transition-opacity"
                aria-label="Download on the App Store"
              >
                <div className="bg-black text-white rounded-lg px-3 py-2 flex items-center space-x-2">
                  <div className="text-white">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
                      <circle cx="12" cy="12" r="1.5" fill="white" opacity="0.3"/>
                      <path d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm0 6c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z" opacity="0.6"/>
                    </svg>
                  </div>
                  <div className="text-xs">
                    <div className="text-[10px] leading-none">Download on the</div>
                    <div className="text-sm font-semibold leading-none">App Store</div>
                  </div>
                </div>
              </a>
              <a
                href="#"
                className="block w-full max-w-[140px] hover:opacity-80 transition-opacity"
                aria-label="Get it on Google Play"
              >
                <div className="bg-black text-white rounded-lg px-3 py-2 flex items-center space-x-2">
                  <div className="text-white">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                      <defs>
                        <linearGradient id="playGradient1" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor="#00D4FF"/>
                          <stop offset="100%" stopColor="#0099CC"/>
                        </linearGradient>
                        <linearGradient id="playGradient2" x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stopColor="#FFD500"/>
                          <stop offset="100%" stopColor="#FF9500"/>
                        </linearGradient>
                        <linearGradient id="playGradient3" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor="#FF4444"/>
                          <stop offset="100%" stopColor="#CC0000"/>
                        </linearGradient>
                        <linearGradient id="playGradient4" x1="0%" y1="100%" x2="100%" y2="0%">
                          <stop offset="0%" stopColor="#00E676"/>
                          <stop offset="100%" stopColor="#00C853"/>
                        </linearGradient>
                      </defs>
                      <path d="M3,20.5V3.5C3,2.91 3.34,2.39 3.84,2.15L13.69,12L3.84,21.85C3.34,21.6 3,21.09 3,20.5Z" fill="url(#playGradient1)"/>
                      <path d="M16.81,15.12L6.05,21.34L14.54,12.85L16.81,15.12Z" fill="url(#playGradient2)"/>
                      <path d="M20.16,10.81C20.5,11.08 20.75,11.5 20.75,12C20.75,12.5 20.53,12.9 20.18,13.18L17.89,14.5L15.39,12L17.89,9.5L20.16,10.81Z" fill="url(#playGradient3)"/>
                      <path d="M6.05,2.66L16.81,8.88L14.54,11.15L6.05,2.66Z" fill="url(#playGradient4)"/>
                    </svg>
                  </div>
                  <div className="text-xs">
                    <div className="text-[10px] leading-none">Get it on</div>
                    <div className="text-sm font-semibold leading-none">Google Play</div>
                  </div>
                </div>
              </a>
            </div>
          </div>
        </div>

        {/* Social Media & Copyright */}
        <div className="mt-12 pt-6 border-t border-border-light">
          <div className="flex flex-col md:flex-row md:justify-between md:items-center">
            <div className="mb-4 md:mb-0">
              <p className="text-copy-light">© 2025 Banwee Store. All Rights Reserved.</p>
            </div>
            <nav className="flex space-x-6" aria-label="Social media links">
              <a 
                href={SOCIAL_MEDIA_LINKS.facebook.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-copy-lighter hover:text-primary transition-colors duration-200 ease-in-out transform hover:scale-110"
                aria-label={SOCIAL_MEDIA_LINKS.facebook.ariaLabel}
                title={SOCIAL_MEDIA_LINKS.facebook.name}
              >
                <FacebookIcon size={20} />
              </a>
              <a 
                href={SOCIAL_MEDIA_LINKS.twitter.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-copy-lighter hover:text-primary transition-colors duration-200 ease-in-out transform hover:scale-110"
                aria-label={SOCIAL_MEDIA_LINKS.twitter.ariaLabel}
                title={SOCIAL_MEDIA_LINKS.twitter.name}
              >
                <TwitterIcon size={20} />
              </a>
              <a 
                href={SOCIAL_MEDIA_LINKS.instagram.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-copy-lighter hover:text-primary transition-colors duration-200 ease-in-out transform hover:scale-110"
                aria-label={SOCIAL_MEDIA_LINKS.instagram.ariaLabel}
                title={SOCIAL_MEDIA_LINKS.instagram.name}
              >
                <InstagramIcon size={20} />
              </a>
              {SOCIAL_MEDIA_LINKS.youtube && (
                <a 
                  href={SOCIAL_MEDIA_LINKS.youtube.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-copy-lighter hover:text-primary transition-colors duration-200 ease-in-out transform hover:scale-110"
                  aria-label={SOCIAL_MEDIA_LINKS.youtube.ariaLabel}
                  title={SOCIAL_MEDIA_LINKS.youtube.name}
                >
                  <YoutubeIcon size={20} />
                </a>
              )}
              <a 
                href={SOCIAL_MEDIA_LINKS.linkedin.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-copy-lighter hover:text-primary transition-colors duration-200 ease-in-out transform hover:scale-110"
                aria-label={SOCIAL_MEDIA_LINKS.linkedin.ariaLabel}
                title={SOCIAL_MEDIA_LINKS.linkedin.name}
              >
                <LinkedinIcon size={20} />
              </a>
            </nav>
          </div>
        </div>
      </div>
    </footer>
  );
};