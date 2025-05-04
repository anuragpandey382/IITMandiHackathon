// When this form gets a POST request, use spawn child to run rem.py script in public folder

import { NextResponse } from 'next/server';
import path from 'path';
import { spawn } from 'child_process';

export async function GET() {
  return new Promise((resolve) => {
    const scriptPath = path.join(process.cwd(), 'public', 'rem.py');
    const child = spawn('python3', [scriptPath]);

    child.stdout.on('data', (data) => {
      console.log(`Script output: ${data}`);
    });

    child.stderr.on('data', (data) => {
      console.error(`Script error: ${data}`);
    });

    child.on('close', (code) => {
      if (code === 0) {
        resolve(NextResponse.json({ message: "Success" }));
      } else {
        resolve(NextResponse.json({ error: "Failed to run script" }, { status: 500 }));
      }
    });
  });
}