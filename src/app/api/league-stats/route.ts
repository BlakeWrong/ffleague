import { NextRequest, NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import { join } from 'path'

export async function GET(request: NextRequest) {
  try {
    console.log('Reading league data from JSON file...');

    // Read the pre-generated league data
    const filePath = join(process.cwd(), 'league_data.json');
    const fileContent = await readFile(filePath, 'utf8');
    const data = JSON.parse(fileContent);

    console.log('Successfully read league data');
    return NextResponse.json(data);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      {
        error: 'Failed to read league data',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}