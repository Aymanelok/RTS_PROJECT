import Header from './Header.jsx';
import Sidebar from './Sidebar.jsx';

export default function DashboardLayout({ now, activePage, onPageChange, children }) {
  return (
    <div className="min-h-screen text-slate-100">
      <Header now={now} />
      <div className="flex">
        <Sidebar activePage={activePage} onPageChange={onPageChange} />
        <main className="w-full flex-1 p-4 lg:p-6">{children}</main>
      </div>
    </div>
  );
}
