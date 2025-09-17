import { NextResponse } from 'next/server'

export async function GET() {
  try {
    const pythonApiUrl = process.env.NODE_ENV === 'production'
      ? `http://localhost:${parseInt(process.env.PORT || '3000') + 1}`
      : 'http://localhost:8001';

    const fullUrl = `${pythonApiUrl}/team-legacy`;

    console.log(`Fetching team legacy data from: ${fullUrl}`)

    const response = await fetch(fullUrl)

    if (!response.ok) {
      console.error(`Python API error: ${response.status} ${response.statusText}`)
      const errorText = await response.text()
      console.error(`Error details: ${errorText}`)
      throw new Error(`Failed to fetch team legacy data: ${response.status}`)
    }

    const data = await response.json()
    console.log('Team legacy data received:', JSON.stringify(data, null, 2))

    return NextResponse.json(data)
  } catch (error) {
    console.error('Error in team legacy API route:', error)
    return NextResponse.json(
      { error: 'Failed to fetch team legacy data' },
      { status: 500 }
    )
  }
}