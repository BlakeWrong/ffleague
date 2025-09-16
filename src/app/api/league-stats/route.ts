import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    console.log('Fetching league data from Python API...');

    // Get the year parameter if provided
    const { searchParams } = new URL(request.url);
    const year = searchParams.get('year');

    // Use different API URLs for development vs production
    const isProd = process.env.NODE_ENV === 'production';
    const herokuPort = process.env.PORT ? parseInt(process.env.PORT) : 3000;
    const pythonPort = isProd ? (herokuPort + 1) : 8001;
    const pythonBaseUrl = `http://localhost:${pythonPort}`;

    // Determine which Python API endpoint to call
    const pythonApiUrl = year
      ? `${pythonBaseUrl}/league/stats/${year}`
      : `${pythonBaseUrl}/league/stats`;

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
    console.log('Successfully fetched league data from Python API');
    return NextResponse.json(data);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      {
        error: 'Failed to fetch league data from Python API',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}