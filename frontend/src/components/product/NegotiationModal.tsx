import React, { useState, useEffect, useRef } from 'react';
import { X, DollarSign, TrendingUp, TrendingDown, CheckCircle, XCircle, Clock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { apiClient } from '../../apis/client';

interface NegotiationRound {
  round: number;
  buyer_offer?: number;
  seller_offer?: number;
  message: string;
  finished: boolean;
  final_price?: number;
}

interface NegotiationModalProps {
  isOpen: boolean;
  onClose: () => void;
  product: {
    id: string;
    name: string;
    price: number;
  };
  onDealAccepted?: (finalPrice: number) => void;
}

const NEGOTIATION_STYLES = [
  { value: 'aggressive', label: 'Aggressive', description: 'Push hard for lower prices' },
  { value: 'balanced', label: 'Balanced', description: 'Moderate negotiation approach' },
  { value: 'friendly', label: 'Friendly', description: 'Cooperative and patient approach' },
];

export const NegotiationModal: React.FC<NegotiationModalProps> = ({
  isOpen,
  onClose,
  product,
  onDealAccepted,
}) => {
  const [targetPrice, setTargetPrice] = useState<string>('');
  const [limitPrice, setLimitPrice] = useState<string>('');
  const [negotiationStyle, setNegotiationStyle] = useState<string>('balanced');
  const [isNegotiating, setIsNegotiating] = useState(false);
  const [negotiationId, setNegotiationId] = useState<string | null>(null);
  const [rounds, setRounds] = useState<NegotiationRound[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState<'setup' | 'negotiating' | 'completed'>('setup');
  const [error, setError] = useState<string | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setTargetPrice('');
      setLimitPrice('');
      setNegotiationStyle('balanced');
      setIsNegotiating(false);
      setNegotiationId(null);
      setRounds([]);
      setCurrentStep('setup');
      setError(null);
    } else {
      // Clear polling when modal closes
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    }
  }, [isOpen]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const handleStartNegotiation = async () => {
    if (!targetPrice || !limitPrice) {
      toast.error('Please enter both target and limit prices');
      return;
    }

    const target = parseFloat(targetPrice);
    const limit = parseFloat(limitPrice);

    if (target <= 0 || limit <= 0) {
      toast.error('Prices must be greater than 0');
      return;
    }

    if (target > limit) {
      toast.error('Target price cannot be higher than limit price');
      return;
    }

    if (limit > product.price) {
      toast.error('Limit price cannot be higher than the product price');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.startNegotiation(
        {
          name: 'Buyer',
          target_price: target,
          limit_price: limit,
          style: negotiationStyle,
        },
        {
          name: 'Seller',
          target_price: product.price,
          limit_price: product.price * 0.8, // Seller willing to go down to 80% of original price
          style: 'balanced',
        }
      );

      if (response.success) {
        setNegotiationId(response.data.negotiation_id);
        setIsNegotiating(true);
        setCurrentStep('negotiating');
        toast.success('Negotiation started!');
        
        // Start polling for negotiation updates
        startPolling(response.data.negotiation_id);
      }
    } catch (error) {
      console.error('Failed to start negotiation:', error);
      setError(error.message || 'Failed to start negotiation. Please try again.');
      toast.error('Failed to start negotiation. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const startPolling = (id: string) => {
    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    // Start new polling interval
    pollingIntervalRef.current = setInterval(async () => {
      await pollNegotiationStatus(id);
    }, 2000);

    // Also poll immediately
    pollNegotiationStatus(id);
  };

  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  const pollNegotiationStatus = async (id: string) => {
    try {
      const response = await apiClient.getNegotiationState(id);
      if (response.success) {
        const state = response.data;
        
        // Add new round to history
        const newRound: NegotiationRound = {
          round: state.round,
          buyer_offer: state.buyer_current_offer,
          seller_offer: state.seller_current_offer,
          message: state.message,
          finished: state.finished,
          final_price: state.final_price,
        };

        setRounds(prev => {
          const existing = prev.find(r => r.round === newRound.round);
          if (existing) {
            return prev.map(r => r.round === newRound.round ? newRound : r);
          }
          return [...prev, newRound];
        });

        if (state.finished) {
          setCurrentStep('completed');
          setIsNegotiating(false);
          stopPolling();
          if (state.final_price) {
            toast.success(`Deal reached at $${state.final_price.toFixed(2)}!`);
          }
        }
      }
    } catch (error) {
      console.error('Failed to get negotiation status:', error);
      setError('Failed to get negotiation updates. Please try refreshing.');
      setIsNegotiating(false);
      stopPolling();
    }
  };

  const handleNextRound = async () => {
    if (!negotiationId) return;

    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.stepNegotiation(negotiationId);

      if (response.success) {
        toast.info('Negotiation round initiated...');
        // Polling will automatically pick up the updates
      }
    } catch (error) {
      console.error('Failed to advance negotiation:', error);
      setError(error.message || 'Failed to advance negotiation. Please try again.');
      toast.error('Failed to advance negotiation. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAcceptDeal = () => {
    const lastRound = rounds[rounds.length - 1];
    if (lastRound?.final_price) {
      onDealAccepted?.(lastRound.final_price);
      toast.success(`Deal accepted at $${lastRound.final_price.toFixed(2)}!`);
      onClose();
    }
  };

  const handleRejectDeal = () => {
    toast.info('Deal rejected. You can start a new negotiation anytime.');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Negotiate Price</h2>
              <p className="text-sm text-gray-600">{product.name}</p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X size={24} />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center">
                  <XCircle className="text-red-600 mr-2" size={20} />
                  <span className="font-medium text-red-900">Error</span>
                </div>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            )}

            {currentStep === 'setup' && (
              <div className="space-y-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <DollarSign className="text-blue-600 mr-2" size={20} />
                    <span className="font-medium text-blue-900">Current Price: ${product.price.toFixed(2)}</span>
                  </div>
                  <p className="text-sm text-blue-700">
                    Set your target and maximum prices to start negotiating with the seller.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Target Price"
                    type="number"
                    step="0.01"
                    min="0"
                    max={product.price}
                    value={targetPrice}
                    onChange={(e) => setTargetPrice(e.target.value)}
                    placeholder="Your ideal price"
                    helperText="The price you'd like to pay"
                  />
                  <Input
                    label="Maximum Price"
                    type="number"
                    step="0.01"
                    min="0"
                    max={product.price}
                    value={limitPrice}
                    onChange={(e) => setLimitPrice(e.target.value)}
                    placeholder="Your maximum budget"
                    helperText="The highest you're willing to pay"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Negotiation Style
                  </label>
                  <div className="grid grid-cols-1 gap-3">
                    {NEGOTIATION_STYLES.map((style) => (
                      <label
                        key={style.value}
                        className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                          negotiationStyle === style.value
                            ? 'border-primary bg-primary/5'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <input
                          type="radio"
                          name="negotiationStyle"
                          value={style.value}
                          checked={negotiationStyle === style.value}
                          onChange={(e) => setNegotiationStyle(e.target.value)}
                          className="sr-only"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{style.label}</div>
                          <div className="text-sm text-gray-600">{style.description}</div>
                        </div>
                        {negotiationStyle === style.value && (
                          <CheckCircle className="text-primary" size={20} />
                        )}
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {currentStep === 'negotiating' && (
              <div className="space-y-6">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <Clock className="text-yellow-600 mr-2" size={20} />
                    <span className="font-medium text-yellow-900">Negotiation in Progress</span>
                  </div>
                  <p className="text-sm text-yellow-700">
                    The negotiation is running automatically. You can watch the rounds below.
                  </p>
                </div>

                {rounds.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="font-medium text-gray-900">Negotiation Rounds</h3>
                    <div className="space-y-3 max-h-60 overflow-y-auto">
                      {rounds.map((round) => (
                        <motion.div
                          key={round.round}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="bg-gray-50 border border-gray-200 rounded-lg p-4"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-gray-900">Round {round.round}</span>
                            {round.finished && (
                              <CheckCircle className="text-green-600" size={20} />
                            )}
                          </div>
                          <p className="text-sm text-gray-700 mb-2">{round.message}</p>
                          {round.buyer_offer && round.seller_offer && (
                            <div className="flex items-center justify-between text-sm">
                              <div className="flex items-center text-blue-600">
                                <TrendingDown size={16} className="mr-1" />
                                Your offer: ${round.buyer_offer.toFixed(2)}
                              </div>
                              <div className="flex items-center text-red-600">
                                <TrendingUp size={16} className="mr-1" />
                                Seller offer: ${round.seller_offer.toFixed(2)}
                              </div>
                            </div>
                          )}
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

                {isNegotiating && (
                  <div className="flex justify-center">
                    <Button
                      onClick={handleNextRound}
                      isLoading={isLoading}
                      disabled={isLoading}
                    >
                      Continue Negotiation
                    </Button>
                  </div>
                )}
              </div>
            )}

            {currentStep === 'completed' && (
              <div className="space-y-6">
                {rounds.length > 0 && rounds[rounds.length - 1].finished && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <CheckCircle className="text-green-600 mr-2" size={20} />
                      <span className="font-medium text-green-900">
                        Deal Reached!
                      </span>
                    </div>
                    <p className="text-sm text-green-700 mb-3">
                      Final price: ${rounds[rounds.length - 1].final_price?.toFixed(2)}
                    </p>
                    <div className="flex space-x-3">
                      <Button
                        onClick={handleAcceptDeal}
                        variant="success"
                        size="sm"
                      >
                        Accept Deal
                      </Button>
                      <Button
                        onClick={handleRejectDeal}
                        variant="outline"
                        size="sm"
                      >
                        Reject Deal
                      </Button>
                    </div>
                  </div>
                )}

                {rounds.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="font-medium text-gray-900">Final Negotiation Summary</h3>
                    <div className="space-y-3 max-h-60 overflow-y-auto">
                      {rounds.map((round) => (
                        <div
                          key={round.round}
                          className="bg-gray-50 border border-gray-200 rounded-lg p-4"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-gray-900">Round {round.round}</span>
                            {round.finished && (
                              <CheckCircle className="text-green-600" size={20} />
                            )}
                          </div>
                          <p className="text-sm text-gray-700 mb-2">{round.message}</p>
                          {round.buyer_offer && round.seller_offer && (
                            <div className="flex items-center justify-between text-sm">
                              <div className="flex items-center text-blue-600">
                                <TrendingDown size={16} className="mr-1" />
                                Your offer: ${round.buyer_offer.toFixed(2)}
                              </div>
                              <div className="flex items-center text-red-600">
                                <TrendingUp size={16} className="mr-1" />
                                Seller offer: ${round.seller_offer.toFixed(2)}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-6 border-t border-gray-200">
            <Button
              onClick={onClose}
              variant="outline"
            >
              {currentStep === 'completed' ? 'Close' : 'Cancel'}
            </Button>
            
            {currentStep === 'setup' && (
              <Button
                onClick={handleStartNegotiation}
                isLoading={isLoading}
                disabled={!targetPrice || !limitPrice || isLoading}
              >
                Start Negotiation
              </Button>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};