import dagre from 'dagre'
import type { WorkflowNode } from '../stores/workflowStore'
import type { Edge } from '@xyflow/react'

const NODE_WIDTH = 180
const NODE_HEIGHT = 80

export function getLayoutedElements(nodes: WorkflowNode[], edges: Edge[], direction: 'LR' | 'TB' = 'LR') {
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setDefaultEdgeLabel(() => ({}))

  const isHorizontal = direction === 'LR'
  dagreGraph.setGraph({ rankdir: direction, nodesep: 60, ranksep: 120, marginx: 40, marginy: 40 })

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
  })

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target)
  })

  dagre.layout(dagreGraph)

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id)
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - NODE_WIDTH / 2,
        y: nodeWithPosition.y - NODE_HEIGHT / 2,
      },
    }
  })

  return { nodes: layoutedNodes, edges }
}
