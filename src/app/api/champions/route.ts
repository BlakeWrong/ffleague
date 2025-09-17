import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const year = searchParams.get('year')

    const pythonApiUrl = process.env.NODE_ENV === 'production'
      ? `http://localhost:${parseInt(process.env.PORT || '3000') + 1}`
      : 'http://localhost:8001';

    const apiPath = year ? `/champions/${year}` : '/champions';
    const fullUrl = `${pythonApiUrl}${apiPath}`;

    console.log(`Fetching champions data from: ${fullUrl}`)

    const response = await fetch(fullUrl)

    if (!response.ok) {
      console.error(`Python API error: ${response.status} ${response.statusText}`)
      const errorText = await response.text()
      console.error(`Error details: ${errorText}`)
      throw new Error(`Failed to fetch champions data: ${response.status}`)
    }

    const data = await response.json()
    console.log('Champions data received:', JSON.stringify(data, null, 2))

    return NextResponse.json(data)
  } catch (error) {
    console.error('Error in champions API route:', error)
    return NextResponse.json(
      { error: 'Failed to fetch champions data' },
      { status: 500 }
    )
  }
}