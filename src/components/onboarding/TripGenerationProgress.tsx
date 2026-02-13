import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  Sparkles, 
  Cloud, 
  Package, 
  CheckCircle2, 
  Loader2,
  Clock
} from "lucide-react";

interface TripGenerationProgressProps {
  jobStatus: 'pending' | 'processing' | 'completed' | 'failed';
  elapsedSeconds: number;
  travelerCount: number;
}

interface GenerationPhase {
  id: string;
  label: string;
  icon: React.ReactNode;
  description: string;
}

const phases: GenerationPhase[] = [
  {
    id: 'analyzing',
    label: 'Analyzing your trip details',
    icon: <Sparkles className="w-5 h-5" />,
    description: 'Processing destination, dates, and travelers'
  },
  {
    id: 'weather',
    label: 'Fetching weather forecast',
    icon: <Cloud className="w-5 h-5" />,
    description: 'Getting real-time weather data for your dates'
  },
  {
    id: 'packing',
    label: 'Building personalized packing lists',
    icon: <Package className="w-5 h-5" />,
    description: 'Creating custom lists for each traveler'
  },
  {
    id: 'finalizing',
    label: 'Adding final touches',
    icon: <CheckCircle2 className="w-5 h-5" />,
    description: 'Organizing and optimizing your lists'
  }
];

export function TripGenerationProgress({ 
  jobStatus, 
  elapsedSeconds, 
  travelerCount 
}: TripGenerationProgressProps) {
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState(0);
  const [showSlowMessage, setShowSlowMessage] = useState(false);

  // Determine current phase based on elapsed time and status
  useEffect(() => {
    if (jobStatus === 'completed') {
      setCurrentPhaseIndex(phases.length);
      return;
    }

    if (jobStatus === 'pending') {
      setCurrentPhaseIndex(0);
    } else if (jobStatus === 'processing') {
      // Progress through phases based on elapsed time
      // Rough estimate: 90 seconds total, ~22 seconds per phase
      const phaseIndex = Math.min(
        Math.floor(elapsedSeconds / 22),
        phases.length - 1
      );
      setCurrentPhaseIndex(phaseIndex);
    }
  }, [elapsedSeconds, jobStatus]);

  // Show slow message after 30 seconds
  useEffect(() => {
    if (elapsedSeconds >= 30) {
      setShowSlowMessage(true);
    }
  }, [elapsedSeconds]);

  // Calculate overall progress percentage
  const progressPercentage = jobStatus === 'completed' 
    ? 100 
    : Math.min((elapsedSeconds / 90) * 100, 95);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  return (
    <div className="w-full max-w-2xl space-y-6">
      {/* Main Progress Card */}
      <Card className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
              <Loader2 className="w-6 h-6 text-primary" />
            </motion.div>
            <div>
              <h2 className="text-xl font-semibold text-secondary">
                Creating Your Packing List
              </h2>
              <p className="text-sm text-muted-foreground">
                {travelerCount} traveler{travelerCount !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Clock className="w-4 h-4" />
            <span className="text-sm font-medium">{formatTime(elapsedSeconds)}</span>
          </div>
        </div>

        {/* Overall Progress Bar */}
        <div className="space-y-2">
          <Progress value={progressPercentage} className="h-2" />
          <p className="text-xs text-muted-foreground text-right">
            {Math.round(progressPercentage)}% complete
          </p>
        </div>

        {/* Phase Stepper */}
        <div className="space-y-3">
          {phases.map((phase, index) => {
            const isCompleted = index < currentPhaseIndex;
            const isActive = index === currentPhaseIndex;
            const isPending = index > currentPhaseIndex;

            return (
              <motion.div
                key={phase.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`flex items-start gap-3 p-3 rounded-lg transition-colors ${
                  isActive 
                    ? 'bg-primary/10 border-2 border-primary/30' 
                    : isCompleted
                    ? 'bg-muted/50'
                    : 'bg-muted/30'
                }`}
              >
                {/* Icon */}
                <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                  isCompleted 
                    ? 'bg-primary text-primary-foreground' 
                    : isActive
                    ? 'bg-primary/20 text-primary'
                    : 'bg-muted text-muted-foreground'
                }`}>
                  {isCompleted ? (
                    <CheckCircle2 className="w-5 h-5" />
                  ) : isActive ? (
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    >
                      {phase.icon}
                    </motion.div>
                  ) : (
                    phase.icon
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className={`font-medium ${
                      isActive ? 'text-primary' : 'text-secondary'
                    }`}>
                      {phase.label}
                    </p>
                    {isActive && (
                      <Badge variant="secondary" className="text-xs">
                        In Progress
                      </Badge>
                    )}
                    {isCompleted && (
                      <Badge variant="default" className="text-xs">
                        Done
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {phase.description}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Slow Message */}
        {showSlowMessage && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4"
          >
            <p className="text-sm text-amber-900 dark:text-amber-200">
              <strong>Still working on your list...</strong> Complex trips with multiple travelers can take up to 2 minutes. We're making sure everything is perfect!
            </p>
          </motion.div>
        )}
      </Card>

      {/* Preview Skeleton Cards */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Package className="w-5 h-5 text-muted-foreground" />
          <h3 className="text-lg font-semibold text-secondary">
            Preview: Your Packing Lists
          </h3>
        </div>
        
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: Math.min(travelerCount * 2, 6) }).map((_, index) => (
            <PackingItemSkeleton key={index} delay={index * 0.1} />
          ))}
        </div>
      </div>
    </div>
  );
}

// Skeleton component for packing list items
function PackingItemSkeleton({ delay }: { delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
    >
      <Card className="p-4 space-y-3">
        <div className="flex items-center gap-3">
          <Skeleton className="w-10 h-10 rounded-lg" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
        <div className="space-y-2">
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-5/6" />
        </div>
      </Card>
    </motion.div>
  );
}