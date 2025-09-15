import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import { promisify } from 'util'

export async function GET(request: NextRequest) {
  try {
    // Call Python script to get ESPN data
    const pythonScript = `
import sys
import os
sys.path.append('${process.cwd()}')
from api_helpers import get_league_stats
import json

try:
    data = get_league_stats()
    print(json.dumps(data))
except Exception as e:
    print(json.dumps({"error": str(e)}), file=sys.stderr)
    sys.exit(1)
`;

    const python = spawn('python3', ['-c', pythonScript], {
      cwd: process.cwd(),
      env: { ...process.env }
    });

    let stdout = '';
    let stderr = '';

    python.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    python.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    const exitCode = await new Promise((resolve) => {
      python.on('close', resolve);
    });

    if (exitCode !== 0) {
      console.error('Python script error:', stderr);
      return NextResponse.json(
        { error: 'Failed to fetch league data', details: stderr },
        { status: 500 }
      );
    }

    const data = JSON.parse(stdout.trim());

    if (data.error) {
      throw new Error(data.error);
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      {
        error: 'Failed to fetch league data',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}