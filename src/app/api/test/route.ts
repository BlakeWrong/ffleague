import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  console.log('Test API called');

  return NextResponse.json({
    message: 'Test API working',
    timestamp: new Date().toISOString()
  });
}