import { Link } from 'react-router-dom';
import { MapPinIcon, MailIcon, PhoneIcon, ArrowRightIcon, FacebookIcon, TwitterIcon, InstagramIcon, YoutubeIcon, LinkedinIcon } from 'lucide-react';
import { SOCIAL_MEDIA_LINKS } from '../../lib/social-media-config';

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
        {/* Newsletter */}
        <div className="bg-background rounded-lg p-6 md:p-10 mb-12">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div className="mb-6 md:mb-0 md:mr-8">
              <h3 className="text-2xl font-bold text-main mb-3">Subscribe to our Newsletter</h3>
              <p className="text-copy-light">Get the latest updates on new products and upcoming sales</p>
            </div>
            <div className="flex-shrink-0 w-full md:w-auto md:min-w-[350px]">
              <form className="flex flex-col sm:flex-row">
                <input
                  type="email"
                  placeholder="Your email address"
                  className="flex-grow px-4 py-3 border border-border rounded-md sm:rounded-l-md sm:rounded-r-none focus:outline-none focus:ring-1 focus:ring-primary bg-surface text-copy mb-2 sm:mb-0"
                />
                <button
                  type="submit"
                  className="bg-primary text-white px-6 py-3 rounded-md sm:rounded-r-md sm:rounded-l-none hover:bg-primary-dark transition-colors flex items-center justify-center whitespace-nowrap">
                  Subscribe
                  <ArrowRightIcon size={16} className="ml-2" />
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* Main Footer */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 lg:gap-12">
          {/* Company Info */}
          <div className="lg:col-span-2">
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