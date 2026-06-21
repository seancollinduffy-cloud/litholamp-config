import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const backendUrl = 'http://127.0.0.1:8001/api/generate';
    const res = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': req.headers.get('content-type') || '',
      },
      body: req.body,
      // @ts-ignore
      duplex: 'half'
    });
    
    if (!res.ok) {
      console.error('Backend proxy error:', res.status, res.statusText);
      const text = await res.text();
      console.error(text);
      return NextResponse.json({ error: 'Backend error' }, { status: res.status });
    }
    
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Proxy exception:', error);
    return NextResponse.json({ error: 'Proxy error' }, { status: 500 });
  }
}
