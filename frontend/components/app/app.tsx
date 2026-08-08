'use client';

import { useEffect, useMemo } from 'react';
import { TokenSource } from 'livekit-client';
import { useSession } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react/dist/ssr';
import type { AppConfig } from '@/app-config';
import { AgentSessionProvider } from '@/components/agents-ui/agent-session-provider';
import { StartAudioButton } from '@/components/agents-ui/start-audio-button';
import { ViewController } from '@/components/app/view-controller';
import { Toaster } from '@/components/ui/sonner';
import { useAgentErrors } from '@/hooks/useAgentErrors';
import { useDebugMode } from '@/hooks/useDebug';
import { getSandboxTokenSource } from '@/lib/utils';
import { toast } from 'sonner';

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';

function AppSetup() {
  useDebugMode({ enabled: IN_DEVELOPMENT });
  useAgentErrors();

  return null;
}

/**
 * Handles microphone permission problems.
 *
 * This is separate from LiveKit's agent error handling because
 * browser microphone permissions can fail before the LiveKit
 * agent enters the "failed" state.
 */
function MicrophonePermissionHandler() {
  useEffect(() => {
    let permissionStatus: PermissionStatus | null = null;

    const showMicrophoneError = () => {
      toast.error('Microphone access is blocked', {
        description:
          'Bharat Buddy needs your microphone to hear you. Click the microphone/lock icon near the address bar, allow microphone access, and reload the page.',
        duration: 10000,
      });
    };

    const checkPermission = async () => {
      try {
        // Check whether the browser supports the Permissions API.
        if (!navigator.permissions) {
          return;
        }

        permissionStatus = await navigator.permissions.query({
          name: 'microphone' as PermissionName,
        });

        if (permissionStatus.state === 'denied') {
          showMicrophoneError();
        }

        permissionStatus.onchange = () => {
          if (permissionStatus?.state === 'denied') {
            showMicrophoneError();
          }
        };
      } catch (error) {
        console.log('Microphone permission check unavailable:', error);
      }
    };

    checkPermission();

    return () => {
      if (permissionStatus) {
        permissionStatus.onchange = null;
      }
    };
  }, []);

  return null;
}

interface AppProps {
  appConfig: AppConfig;
}

export function App({ appConfig }: AppProps) {
  const tokenSource = useMemo(() => {
    return typeof process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT === 'string'
      ? getSandboxTokenSource(appConfig)
      : TokenSource.endpoint('/api/token');
  }, [appConfig]);

  const session = useSession(
    tokenSource,
    appConfig.agentName ? { agentName: appConfig.agentName } : undefined
  );

  return (
    <AgentSessionProvider session={session}>
      <AppSetup />

      {/* Microphone permission handling */}
      <MicrophonePermissionHandler />

      <main className="grid h-svh grid-cols-1 place-content-center">
        <ViewController appConfig={appConfig} />
      </main>

      <StartAudioButton label="Start Audio" />

      <Toaster
        icons={{
          warning: <WarningIcon weight="bold" />,
        }}
        position="top-center"
        className="toaster group"
        style={
          {
            '--normal-bg': 'var(--popover)',
            '--normal-text': 'var(--popover-foreground)',
            '--normal-border': 'var(--border)',
          } as React.CSSProperties
        }
      />
    </AgentSessionProvider>
  );
}