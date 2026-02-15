import "./globals.css";

export const metadata = {
  title: "MeetFriends Demo",
  description: "Personalized feed with tunable ranking pipeline",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
