import React from "react";
import { Loader2, X } from "lucide-react";

export function Spinner({ className="h-4 w-4" }:{className?:string}) {
  return <Loader2 className={`animate-spin ${className}`}/>;
}
export function PageLoader() {
  return <div className="flex h-64 items-center justify-center"><Spinner className="h-8 w-8 text-blue-600"/></div>;
}
export function Alert({ type, message }:{type:"error"|"success"|"info"|"warning"; message:string}) {
  const s={error:"bg-red-50 border-red-200 text-red-700",success:"bg-green-50 border-green-200 text-green-700",info:"bg-blue-50 border-blue-200 text-blue-700",warning:"bg-amber-50 border-amber-200 text-amber-700"};
  return <div className={`rounded-lg border px-4 py-3 text-sm ${s[type]}`}>{message}</div>;
}
export function StatusBadge({ active }:{active:boolean}) {
  return <span className={`badge ${active?"bg-green-100 text-green-700":"bg-red-100 text-red-700"}`}>{active?"Активен":"Деактивирован"}</span>;
}
export function Modal({ open, onClose, title, children, size="md" }:{open:boolean;onClose:()=>void;title:string;children:React.ReactNode;size?:"sm"|"md"|"lg"|"xl"}) {
  if (!open) return null;
  const w={sm:"max-w-sm",md:"max-w-md",lg:"max-w-lg",xl:"max-w-2xl"};
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose}/>
      <div className={`relative z-10 w-full ${w[size]} rounded-xl bg-white shadow-2xl max-h-[90vh] flex flex-col`}>
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <h2 className="text-base font-semibold text-gray-900">{title}</h2>
          <button onClick={onClose} className="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"><X className="h-4 w-4"/></button>
        </div>
        <div className="overflow-y-auto p-6">{children}</div>
      </div>
    </div>
  );
}
export function ConfirmModal({ open, onClose, onConfirm, title, message, danger=false, loading=false }:{open:boolean;onClose:()=>void;onConfirm:()=>void;title:string;message:string;danger?:boolean;loading?:boolean}) {
  return (
    <Modal open={open} onClose={onClose} title={title} size="sm">
      <p className="mb-6 text-sm text-gray-600">{message}</p>
      <div className="flex justify-end gap-3">
        <button className="btn-secondary" onClick={onClose} disabled={loading}>Отмена</button>
        <button className={danger?"btn-danger":"btn-primary"} onClick={onConfirm} disabled={loading}>{loading&&<Spinner/>}Подтвердить</button>
      </div>
    </Modal>
  );
}
export function Table({ headers, children }:{headers:string[];children:React.ReactNode}) {
  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-left">
          <tr>{headers.map(h=><th key={h} className="px-4 py-3 font-semibold text-gray-600 border-b border-gray-200 whitespace-nowrap">{h}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">{children}</tbody>
      </table>
    </div>
  );
}
export function EmptyState({ icon, title, description, action }:{icon:React.ReactNode;title:string;description?:string;action?:React.ReactNode}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 text-gray-300">{icon}</div>
      <h3 className="text-base font-semibold text-gray-900">{title}</h3>
      {description&&<p className="mt-1 text-sm text-gray-500">{description}</p>}
      {action&&<div className="mt-4">{action}</div>}
    </div>
  );
}
export function DangerZone({ title="Опасная зона", children }:{title?:string;children:React.ReactNode}) {
  return (
    <div className="mt-8 rounded-xl border-2 border-red-200 bg-red-50">
      <div className="flex items-center gap-2 border-b border-red-200 px-5 py-3">
        <span className="text-base">⚠️</span>
        <h3 className="text-sm font-bold text-red-700 uppercase tracking-wide">{title}</h3>
        <span className="ml-auto rounded-full bg-red-100 px-2 py-0.5 text-xs font-bold text-red-600">КРАЙНЯЯ МЕРА</span>
      </div>
      <div className="p-5 space-y-4">{children}</div>
    </div>
  );
}
