import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    console.log('Fetching league data from Python API...');

    // Get the year parameter if provided
    const { searchParams } = new URL(request.url);
    const year = searchParams.get('year');

    // Determine which Python API endpoint to call
    const pythonApiUrl = year
      ? `http://localhost:8001/league/stats/${year}`
      : 'http://localhost:8001/league/stats';

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