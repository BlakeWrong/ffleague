import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import { promisify } from 'util'

export async function GET(request: NextRequest) {
  try {
    console.log('Starting ESPN API request...');

    // Call Python script to get ESPN data
    const pythonScript = `
import sys
import os
sys.path.append('${process.cwd()}')
from api_helpers import get_league_stats
import json

try:
    print("Starting ESPN API call...", file=sys.stderr)
    data = get_league_stats()
    print("ESPN API call completed", file=sys.stderr)
    print(json.dumps(data))
except Exception as e:
    print(f"Error: {str(e)}", file=sys.stderr)
    print(json.dumps({"error": str(e)}), file=sys.stderr)
    sys.exit(1)
`;

    const python = spawn('python3', ['-c', pythonScript], {
      cwd: process.cwd(),
      env: { ...process.env },
      timeout: 30000 // 30 second timeout
    });

    let stdout = '';
    let stderr = '';

    python.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    python.stderr.on('data', (data) => {
      stderr += data.toString();
      console.log('Python stderr:', data.toString());
    });

    // Add timeout handling
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => {
        python.kill('SIGKILL');
        reject(new Error('Python process timed out after 30 seconds'));
      }, 30000);
    });

    const exitPromise = new Promise((resolve) => {
      python.on('close', resolve);
    });

    const exitCode = await Promise.race([exitPromise, timeoutPromise]);

    if (exitCode !== 0) {
      console.error('Python script error:', stderr);
      return NextResponse.json(
        { error: 'Failed to fetch league data', details: stderr },
        { status: 500 }
      );
    }

    console.log('Python stdout:', stdout);

    if (!stdout.trim()) {
      throw new Error('No output from Python script');
    }

    const data = JSON.parse(stdout.trim());

    if (data.error) {
      throw new Error(data.error);
    }

    console.log('Returning data:', data);
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