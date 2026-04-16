import { cn } from "@/lib/utils";

interface PageContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export default function PageContainer({
  children,
  className,
  ...props
}: PageContainerProps) {
  return (
    <div
      className={cn(
        "max-w-5xl mx-auto w-full px-6 md:px-12 lg:px-16 pt-[104px] pb-20 min-h-screen",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
