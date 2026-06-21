import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest, { params }: { params: Promise<{ job_id: string }> }) {
  try {
    const resolvedParams = await params;
    const { searchParams } = new URL(req.url);
    const hw = searchParams.get('hw') || 'RoundWoodBase';
    
    const backendUrl = `http://127.0.0.1:8001/api/download/${resolvedParams.job_id}?hw=${hw}`;
    
    const res = await fetch(backendUrl, {
      method: 'GET'
    });
    
    if (!res.ok) {
      return new NextResponse('Backend error', { status: res.status });
    }
    
    // Explicitly pipe the stream directly to the client
    const headers = new Headers();
    if (res.headers.has('content-length')) {
        headers.set('content-length', res.headers.get('content-length')!);
    }
    if (res.headers.has('content-type')) {
        headers.set('content-type', res.headers.get('content-type')!);
    }
    if (res.headers.has('content-disposition')) {
        headers.set('content-disposition', res.headers.get('content-disposition')!);
    }
    
    return new NextResponse(res.body, {
      status: 200,
      headers
    });
    
  } catch (error) {
    console.error('Download Proxy exception:', error);
    return new NextResponse('Proxy error', { status: 500 });
  }
}
