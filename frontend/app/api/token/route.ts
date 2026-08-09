import { NextResponse } from 'next/server';
import {
  AccessToken,
  type AccessTokenOptions,
  type VideoGrant,
} from 'livekit-server-sdk';
import { RoomConfiguration } from '@livekit/protocol';

type ConnectionDetails = {
  serverUrl: string;
  roomName: string;
  participantName: string;
  participantToken: string;
};

const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;
const AGENT_NAME = process.env.AGENT_NAME;

export const revalidate = 0;

export async function POST(req: Request) {
  try {
    if (!LIVEKIT_URL) {
      throw new Error('LIVEKIT_URL is not defined');
    }

    if (!API_KEY) {
      throw new Error('LIVEKIT_API_KEY is not defined');
    }

    if (!API_SECRET) {
      throw new Error('LIVEKIT_API_SECRET is not defined');
    }

    // --------------------------------------------------------
    // Parse room configuration
    // --------------------------------------------------------

    const body = await req.json().catch(() => ({}));

    let roomConfig: RoomConfiguration | undefined;

    if (body?.room_config) {
      roomConfig = RoomConfiguration.fromJson(body.room_config, {
        ignoreUnknownFields: true,
      });
    } else if (AGENT_NAME) {
      roomConfig = RoomConfiguration.fromJson(
        {
          agents: [
            {
              agentName: AGENT_NAME,
            },
          ],
        },
        {
          ignoreUnknownFields: true,
        },
      );
    }

    // --------------------------------------------------------
    // Persistent student identity
    // --------------------------------------------------------
    //
    // The frontend sends the student's ID in the request body.
    // If it does not exist yet, create one.
    //
    // IMPORTANT:
    // Do NOT use a random ID for every connection.
    // The same student ID must be reused when reconnecting.
    //

    let participantIdentity = body?.student_id;

    if (
      typeof participantIdentity !== 'string' ||
      participantIdentity.trim() === ''
    ) {
      participantIdentity = `student-${crypto.randomUUID()}`;
    }

    participantIdentity = participantIdentity.trim();

    const participantName = 'user';

    // --------------------------------------------------------
    // New room for every connection is okay.
    // Student identity stays the same.
    // --------------------------------------------------------

    const roomName = `voice_assistant_room_${crypto.randomUUID()}`;

    // --------------------------------------------------------
    // Generate LiveKit participant token
    // --------------------------------------------------------

    const participantToken = await createParticipantToken(
      {
        identity: participantIdentity,
        name: participantName,
      },
      roomName,
      roomConfig,
    );

    // --------------------------------------------------------
    // Return connection details
    // --------------------------------------------------------

    const data: ConnectionDetails = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantName,
      participantToken,
    };

    const headers = new Headers({
      'Cache-Control': 'no-store',
    });

    return NextResponse.json(data, {
      headers,
    });
  } catch (error) {
    console.error('Failed to create LiveKit token:', error);

    if (error instanceof Error) {
      return new NextResponse(error.message, {
        status: 500,
      });
    }

    return new NextResponse('Internal server error', {
      status: 500,
    });
  }
}

// ============================================================
// CREATE PARTICIPANT TOKEN
// ============================================================

function createParticipantToken(
  userInfo: AccessTokenOptions,
  roomName: string,
  roomConfig?: RoomConfiguration,
): Promise<string> {
  const at = new AccessToken(API_KEY!, API_SECRET!, {
    ...userInfo,
    ttl: '15m',
  });

  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };

  at.addGrant(grant);

  if (roomConfig) {
    at.roomConfig = roomConfig;
  }

  return at.toJwt();
}