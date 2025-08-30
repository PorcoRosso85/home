export const metadata = {
  title: 'OpenNext STG',
  description: 'OpenNext on Cloudflare Workers - Staging',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}