"use client";

import { useCallback, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  type Node,
  type Edge,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import Currency from "@/components/Currency";
import type { YtdSummary } from "@/lib/types";
import { formatMarginPct } from "@/lib/ytd";
import { useChartTheme } from "@/lib/theme";
import GlassCard, { SectionLabel, SectionTitle } from "@/components/GlassCard";

type FlowNodeData = {
  label: string;
  amount: number;
  sublabel?: string;
  variant: "revenue" | "cost" | "profit" | "neutral";
  onClick?: () => void;
};

function FlowNode({ data }: NodeProps<Node<FlowNodeData>>) {
  const variantStyles = {
    revenue: "border-accent/40 bg-accent/10 text-accent",
    cost: "border-red/30 bg-red/5 text-red",
    profit: "border-green/40 bg-green/10 text-green",
    neutral: "border-border bg-surface-elevated text-text",
  };

  return (
    <div
      className={`flow-node min-w-[140px] cursor-pointer rounded-xl border-2 px-4 py-3 shadow-lg transition-all duration-200 hover:scale-105 hover:shadow-xl ${variantStyles[data.variant]}`}
      onClick={data.onClick}
    >
      <Handle type="target" position={Position.Left} className="!bg-accent !w-2 !h-2 !border-0" />
      <div className="text-xs font-semibold uppercase tracking-wider opacity-70">{data.label}</div>
      <div className="mt-1 font-mono text-lg font-bold tabular-nums">
        <Currency amount={data.amount} weight="bold" />
      </div>
      {data.sublabel && (
        <div className="mt-0.5 text-[10px] opacity-60">{data.sublabel}</div>
      )}
      <Handle type="source" position={Position.Right} className="!bg-accent !w-2 !h-2 !border-0" />
    </div>
  );
}

const nodeTypes = { flowNode: FlowNode };

interface PLFlowDiagramProps {
  ytd: YtdSummary;
  onNavigate?: (tab: "overview" | "pl" | "balance") => void;
}

export default function PLFlowDiagram({ ytd, onNavigate }: PLFlowDiagramProps) {
  const ct = useChartTheme();

  const nodes: Node<FlowNodeData>[] = useMemo(() => [
    {
      id: "revenue",
      type: "flowNode",
      position: { x: 0, y: 80 },
      data: {
        label: "Net Revenue",
        amount: ytd.ytd_revenue,
        sublabel: "YTD sales",
        variant: "revenue",
        onClick: () => onNavigate?.("overview"),
      },
    },
    {
      id: "cogs",
      type: "flowNode",
      position: { x: 220, y: 0 },
      data: {
        label: "COGS",
        amount: ytd.ytd_cogs,
        sublabel: "Cost of goods",
        variant: "cost",
        onClick: () => onNavigate?.("pl"),
      },
    },
    {
      id: "gross",
      type: "flowNode",
      position: { x: 220, y: 160 },
      data: {
        label: "Gross Profit",
        amount: ytd.ytd_gross_profit,
        variant: "profit",
        onClick: () => onNavigate?.("pl"),
      },
    },
    {
      id: "opex",
      type: "flowNode",
      position: { x: 440, y: 0 },
      data: {
        label: "Operating Exp.",
        amount: ytd.ytd_operating_expenses,
        sublabel: "Salaries, utilities…",
        variant: "cost",
        onClick: () => onNavigate?.("pl"),
      },
    },
    {
      id: "net",
      type: "flowNode",
      position: { x: 440, y: 160 },
      data: {
        label: "Net Profit",
        amount: ytd.ytd_net_profit,
        sublabel: `${formatMarginPct(ytd.ytd_operating_margin)} margin`,
        variant: ytd.ytd_net_profit >= 0 ? "profit" : "cost",
        onClick: () => onNavigate?.("balance"),
      },
    },
  ], [ytd, onNavigate]);

  const edges: Edge[] = useMemo(() => [
    { id: "e-r-c", source: "revenue", target: "cogs", animated: true, style: { stroke: ct.accent, strokeWidth: 2 } },
    { id: "e-r-g", source: "revenue", target: "gross", animated: true, style: { stroke: ct.green, strokeWidth: 2 } },
    { id: "e-g-o", source: "gross", target: "opex", style: { stroke: ct.red, strokeWidth: 1.5, strokeDasharray: "5,5" } },
    { id: "e-g-n", source: "gross", target: "net", animated: true, style: { stroke: ct.green, strokeWidth: 2 } },
    { id: "e-o-n", source: "opex", target: "net", style: { stroke: ct.red, strokeWidth: 1.5 } },
  ], [ct]);

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node<FlowNodeData>) => {
    node.data.onClick?.();
  }, []);

  return (
    <GlassCard className="overflow-hidden" glow>
      <div className="border-b border-border px-6 py-5">
        <SectionLabel>Financial Pipeline</SectionLabel>
        <SectionTitle>P&L Flow — click nodes to explore</SectionTitle>
        <p className="mt-1 text-sm text-text-secondary">
          Interactive view of how revenue flows through costs to net profit
        </p>
      </div>
      <div className="h-[320px] w-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodeClick={onNodeClick}
          fitView
          fitViewOptions={{ padding: 0.3 }}
          proOptions={{ hideAttribution: true }}
          nodesDraggable
          nodesConnectable={false}
          panOnScroll
          zoomOnScroll
        >
          <Background gap={20} size={1} color={ct.grid} />
          <Controls showInteractive={false} className="!rounded-lg !border-border !bg-surface !shadow-lg" />
          <MiniMap
            nodeColor={(n) => {
              const v = (n.data as FlowNodeData)?.variant;
              if (v === "revenue") return ct.accent;
              if (v === "profit") return ct.green;
              if (v === "cost") return ct.red;
              return ct.barSecondary;
            }}
            className="!rounded-lg !border-border !bg-surface"
          />
        </ReactFlow>
      </div>
    </GlassCard>
  );
}
