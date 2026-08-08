import { ReactNode, useEffect } from 'react';
import { toast as sonnerToast } from 'sonner';
import { useAgent, useSessionContext } from '@livekit/components-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface ToastProps {
  title: ReactNode;
  description: ReactNode;
}

function toastAlert(toast: ToastProps) {
  const { title, description } = toast;

  return sonnerToast.custom(
    (id) => (
      <Alert
        onClick={() => sonnerToast.dismiss(id)}
        className="w-full bg-accent md:w-[500px]"
      >
        <AlertTitle>{title}</AlertTitle>
        <AlertDescription>{description}</AlertDescription>
      </Alert>
    ),
    {
      duration: 10_000,
    }
  );
}

export function useAgentErrors() {
  const agent = useAgent();
  const { isConnected, end } = useSessionContext();

  useEffect(() => {
    if (!isConnected || agent.state !== 'failed') {
      return;
    }

    const reasons = agent.failureReasons;

    // Combine all failure reasons into one string
    const errorText = reasons.join(' ').toLowerCase();

    // -----------------------------------------
    // MICROPHONE PERMISSION ERROR
    // -----------------------------------------
    const microphonePermissionDenied =
      errorText.includes('notallowederror') ||
      errorText.includes('permission denied') ||
      errorText.includes('permissiondenied') ||
      errorText.includes('not allowed') ||
      errorText.includes('microphone permission') ||
      errorText.includes('microphone access');

    if (microphonePermissionDenied) {
      toastAlert({
        title: '🎙️ Microphone access is blocked',
        description: (
          <div className="space-y-2">
            <p>
              Bharat Buddy needs microphone access to hear you and help you
              learn.
            </p>

            <p>
              Click the <strong>🔒 lock icon</strong> next to the website
              address, allow <strong>Microphone</strong> access, and then
              reload the page.
            </p>
          </div>
        ),
      });

      end();
      return;
    }

    // -----------------------------------------
    // MICROPHONE / AUDIO DEVICE NOT FOUND
    // -----------------------------------------
    const microphoneNotFound =
      errorText.includes('notfounderror') ||
      errorText.includes('device not found') ||
      errorText.includes('no input device') ||
      errorText.includes('microphone not found');

    if (microphoneNotFound) {
      toastAlert({
        title: '🎙️ Microphone not found',
        description: (
          <div className="space-y-2">
            <p>
              Bharat Buddy could not find a microphone on your device.
            </p>

            <p>
              Please connect a microphone and make sure it is enabled in your
              browser settings, then try again.
            </p>
          </div>
        ),
      });

      end();
      return;
    }

    // -----------------------------------------
    // OTHER AGENT ERRORS
    // -----------------------------------------
    toastAlert({
      title: 'Session ended',
      description: (
        <div className="space-y-2">
          {reasons.length > 1 && (
            <ul className="list-inside list-disc">
              {reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          )}

          {reasons.length === 1 && (
            <p className="w-full">{reasons[0]}</p>
          )}

          <p className="w-full">
            <a
              target="_blank"
              rel="noopener noreferrer"
              href="https://docs.livekit.io/agents/start/voice-ai/"
              className="whitespace-nowrap underline"
            >
              See quickstart guide
            </a>
            .
          </p>
        </div>
      ),
    });

    end();
  }, [agent, isConnected, end]);
}