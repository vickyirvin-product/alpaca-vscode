import { SmartWizard } from '@/components/onboarding/SmartWizard';
import { useApp } from '@/context/AppContext';
import { Dashboard } from '@/components/dashboard/Dashboard';

const Index = () => {
  const { hasCompletedOnboarding } = useApp();

  if (hasCompletedOnboarding) {
    return <Dashboard />;
  }

  return <SmartWizard />;
};

export default Index;
