import { NextResponse } from 'next/server';
import { writeFile, mkdir, readFile } from 'fs/promises';
import { join } from 'path';
import { existsSync } from 'fs';
import { exec } from 'child_process';
import { promisify } from 'util';

const execPromise = promisify(exec);

export async function POST(request) {
  try {
    const formData = await request.formData();
    const files = formData.getAll('files');
    
    if (!files || files.length === 0) {
      return NextResponse.json(
        { error: "No file uploaded" },
        { status: 400 }
      );
    }

    const uploadsDir = join(process.cwd(), 'public/uploads');
    if (!existsSync(uploadsDir)) {
      await mkdir(uploadsDir, { recursive: true });
    }

    const spawnPromises = files.map(async (file) => {
      const bytes = await file.arrayBuffer();
      const buffer = Buffer.from(bytes);
      const fileName = `${Date.now()}-${file.name}`;
      const filePath = join(uploadsDir, fileName);

      await writeFile(filePath, buffer);

      const fileUrl = `/uploads/${fileName}`;
      const fullFilePath = join(process.cwd(), 'public', fileUrl);
      const scriptPath = join(process.cwd(), 'public', 'pipeline.py');
        
      const { stdout, stderr } = await execPromise(`python ${scriptPath} "${fullFilePath}"`);
        
      if (stderr) {
          console.error('Python script error:', stderr);
      } 
    });

    await Promise.all(spawnPromises);

    const jsonPath = join(process.cwd(), "public", "results.json");
    const jsonDataRaw = await readFile(jsonPath, 'utf-8');
    const jsonData = JSON.parse(jsonDataRaw);

    // console.log('JSON Data:', jsonData);
    return NextResponse.json({ 
      success: true, 
      results: jsonData
    });
    
  } 
  catch (error) {
    console.error('Error processing file:', error);
    return NextResponse.json(
      { error: error.message || "Failed to process file" },
      { status: 500 }
    );
  }
}