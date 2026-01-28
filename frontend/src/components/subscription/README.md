# Subscription Components

## Modal Components

### PauseSubscriptionModal

A custom modal component for pausing subscriptions with an optional reason field.

**Features:**
- Custom modal replacing browser `window.alert()`
- Optional reason field (up to 500 characters)
- Loading states with spinner
- Accessible with proper focus management
- Responsive design

### ResumeSubscriptionModal

A custom modal component for resuming paused subscriptions.

**Features:**
- Clear explanation of what happens when resuming
- Shows next billing date information
- Loading states during resume operation
- Confirmation required before proceeding

### CancelSubscriptionModal

A custom modal component for cancelling subscriptions with enhanced safety measures.

**Features:**
- Requires typing "CANCEL" to confirm (prevents accidental cancellation)
- Optional reason field for feedback (up to 500 characters)
- Clear warning about irreversible action
- Loading states during cancellation

## Props

```typescript
interface PauseSubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reason?: string) => void;
  subscriptionId: string;
  planName: string;
  loading?: boolean;
}

interface ResumeSubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  subscriptionId: string;
  planName: string;
  nextBillingDate?: string;
  loading?: boolean;
}

interface CancelSubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reason?: string) => void;
  subscriptionId: string;
  planName: string;
  loading?: boolean;
}
```

## SubscriptionCard Updates

The `SubscriptionCard` component has been updated to use custom modals for all subscription actions:

### Changes

- **onPause prop**: Now accepts `(subscriptionId: string, reason?: string) => void`
- **onCancel prop**: Now accepts `(subscriptionId: string, reason?: string) => void`
- **onResume prop**: Remains `(subscriptionId: string) => void`
- **Custom Modals**: All actions now use custom modals instead of browser dialogs
- **Better UX**: Provides context and explanations before each action

### Migration

Update your subscription handlers to accept the optional reason parameter:

```tsx
// Before
const handlePause = async (subscriptionId: string) => {
  const reason = prompt('Reason for pausing?');
  await pauseSubscription(subscriptionId, reason);
};

const handleCancel = async (subscriptionId: string) => {
  if (confirm('Are you sure?')) {
    await cancelSubscription(subscriptionId);
  }
};

const handleResume = async (subscriptionId: string) => {
  if (confirm('Are you sure?')) {
    await resumeSubscription(subscriptionId);
  }
};

// After
const handlePause = async (subscriptionId: string, reason?: string) => {
  await pauseSubscription(subscriptionId, reason);
};

const handleCancel = async (subscriptionId: string, reason?: string) => {
  await cancelSubscription(subscriptionId, reason);
};

const handleResume = async (subscriptionId: string) => {
  await resumeSubscription(subscriptionId);
};
```

## API Updates

The subscription API has been updated to support reason parameters:

- `cancelSubscription(subscriptionId, reason?)` - Now accepts optional cancellation reason
- `pauseSubscription(subscriptionId, reason?)` - Already supported pause reason
- `resumeSubscription(subscriptionId)` - No changes

All modals handle collecting user input, so you no longer need to use browser dialogs.