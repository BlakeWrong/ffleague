import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const year = searchParams.get('year');
    const week = searchParams.get('week');

    if (!week) {
      return NextResponse.json(
        { error: 'Week parameter is required' },
        { status: 400 }
      );
    }

    const pythonApiUrl = process.env.NODE_ENV === 'production'
      ? `http://localhost:${parseInt(process.env.PORT || '3000') + 1}`
      : 'http://localhost:8001';

    let apiPath: string;
    if (year) {
      apiPath = `/matchups/${year}/${week}`;
    } else {
      apiPath = `/matchups/${week}`;
    }

    const response = await fetch(`${pythonApiUrl}${apiPath}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
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
    return NextResponse.json(data, {
      headers: {
        'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
      },
    });
  } catch (error) {
    console.error('API Route Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}