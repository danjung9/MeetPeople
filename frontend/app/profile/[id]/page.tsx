import ProfileClient from "../../../components/ProfileClient";

export default async function ProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const userId = Number(id || 1);
  return <ProfileClient userId={Number.isNaN(userId) ? 1 : userId} />;
}
