import { NextRequest, NextResponse } from 'next/server';

interface RouteParams {
  params: Promise<{
    week: string;
  }>;
}

export async function GET(
  request: NextRequest,
  { params }: RouteParams
) {
  try {
    const { week } = await params;

    const pythonApiUrl = process.env.NODE_ENV === 'production'
      ? `http://localhost:${parseInt(process.env.PORT || '3000') + 1}`
      : 'http://localhost:8001';

    const response = await fetch(`${pythonApiUrl}/matchups/${week}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Python API Error:', response.status, errorText);
      return NextResponse.json(
        { error: 'Failed to fetch matchups', details: errorText },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('API Route Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}