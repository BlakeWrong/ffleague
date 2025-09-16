import { NextResponse } from 'next/server'

export async function GET() {
  try {
    console.log('Fetching standings data from Python API...');

    // Use different API URLs for development vs production
    const isProd = process.env.NODE_ENV === 'production';
    const herokuPort = process.env.PORT ? parseInt(process.env.PORT) : 3000;
    const pythonPort = isProd ? (herokuPort + 1) : 8001;
    const pythonBaseUrl = `http://localhost:${pythonPort}`;

    const pythonApiUrl = `${pythonBaseUrl}/standings`;

    console.log('Calling:', pythonApiUrl);

    const response = await fetch(pythonApiUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Python API returned ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('Successfully fetched standings data from Python API');

    return NextResponse.json(data);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      {
        error: 'Failed to fetch standings data from Python API',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}