import { BaseEdge, EdgeLabelRenderer, getBezierPath, type EdgeProps } from '@xyflow/react'
import { useWorkflowStore } from '../../stores/workflowStore'

export default function CustomEdge({
  id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data, style, markerEnd, selected,
}: EdgeProps) {
  const selectedEdgeId = useWorkflowStore(s => s.selectedEdgeId)
  const isSelected = selected || selectedEdgeId === id

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition,
  })

  const label = data?.label as string | undefined
  const color = data?.color as string | undefined

  const edgeStyle = isSelected
    ? { ...style, stroke: '#3b82f6', strokeWidth: 3 }
    : style

  return (
    <>
      <BaseEdge path={edgePath} markerEnd={markerEnd} style={edgeStyle} />
      {label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
              backgroundColor: color ? color + '20' : '#1e293b',
              borderColor: color ? color + '40' : '#334155',
            }}
            className="px-2 py-0.5 rounded-full text-[11px] font-semibold border shadow-sm"
          >
            <span style={{ color: color || '#94a3b8' }}>{label}</span>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  )
}
