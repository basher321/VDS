"use client";
import { useRouter } from "next/navigation";
import { use } from "react";
import CertificatePreview from "@/components/certificates/CertificatePreview";

export default function CertificateDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  return <CertificatePreview certId={Number(id)} onClose={() => router.push("/certificates")} />;
}
