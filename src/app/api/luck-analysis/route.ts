import { NextResponse } from 'next/server'

const PYTHON_API_URL = process.env.NODE_ENV === 'production'
  ? `http://localhost:${process.env.PORT ? parseInt(process.env.PORT) + 1 : 8001}`
  : 'http://localhost:8001'

export async function GET() {
  try {
    console.log('Fetching luck analysis from Python API...')

    const response = await fetch(`${PYTHON_API_URL}/luck-analysis`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Python API error:', response.status, errorText)
      throw new Error(`Python API responded with ${response.status}: ${errorText}`)
    }

    const data = await response.json()
    console.log('Successfully fetched luck analysis data')

    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching luck analysis:', error)
    return NextResponse.json(
      { error: 'Failed to fetch luck analysis data' },
      { status: 500 }
    )
  }
}