// Redirect /seo to /oracle (unified)
import { redirect } from 'next/navigation';

export default function SEORedirect() {
    redirect('/oracle');
}
