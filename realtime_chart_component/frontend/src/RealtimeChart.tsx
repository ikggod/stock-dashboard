import React, { useEffect, useRef, useState } from "react"
import { Streamlit, RenderData } from "streamlit-component-lib"
import Plot from "react-plotly.js"

interface ChartProps {
  stock_code: string
  stock_name: string
  avg_price: number
  initial_data: Array<{time: string, price: number}>
  websocket_url?: string
  height: number
}

const RealtimeChart: React.FC = () => {
  const [chartData, setChartData] = useState<Array<{time: string, price: number}>>([])
  const [props, setProps] = useState<ChartProps | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    // Streamlit에서 props 받기
    const onRender = (event: Event) => {
      const data = (event as CustomEvent<RenderData>).detail
      const args = data.args as ChartProps

      setProps(args)
      setChartData(args.initial_data || [])

      // WebSocket 연결 (URL이 있는 경우)
      if (args.websocket_url && !wsRef.current) {
        connectWebSocket(args.websocket_url, args.stock_code)
      }

      // Streamlit에 준비 완료 알림
      Streamlit.setFrameHeight()
    }

    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender)
    Streamlit.setComponentReady()

    return () => {
      Streamlit.events.removeEventListener(Streamlit.RENDER_EVENT, onRender)
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const connectWebSocket = (url: string, stockCode: string) => {
    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        console.log("WebSocket 연결 성공")
        // 종목 구독 메시지 전송
        ws.send(JSON.stringify({
          type: "subscribe",
          stock_code: stockCode
        }))
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          // 새로운 데이터 포인트 추가 (깜빡임 없이 append만)
          if (data.price && data.time) {
            setChartData(prevData => {
              const newData = [...prevData, { time: data.time, price: data.price }]
              // 최근 100개만 유지
              if (newData.length > 100) {
                return newData.slice(-100)
              }
              return newData
            })
          }
        } catch (err) {
          console.error("WebSocket 메시지 파싱 오류:", err)
        }
      }

      ws.onerror = (error) => {
        console.error("WebSocket 에러:", error)
      }

      ws.onclose = () => {
        console.log("WebSocket 연결 종료")
        wsRef.current = null
      }
    } catch (err) {
      console.error("WebSocket 연결 실패:", err)
    }
  }

  if (!props) {
    return <div>Loading...</div>
  }

  // Plotly 차트 데이터
  const plotData = [
    {
      x: chartData.map(d => d.time),
      y: chartData.map(d => d.price),
      type: "scatter",
      mode: "lines",
      line: { color: "#1f77b4", width: 2 },
      name: "현재가"
    },
    {
      // 평단가 라인
      x: chartData.map(d => d.time),
      y: chartData.map(() => props.avg_price),
      type: "scatter",
      mode: "lines",
      line: { color: "orange", dash: "dash", width: 1 },
      name: `평단: ${props.avg_price.toLocaleString()}원`
    }
  ]

  const layout = {
    height: props.height,
    margin: { l: 50, r: 50, t: 30, b: 50 },
    xaxis: {
      title: "시간",
      showgrid: true,
      gridcolor: "rgba(128,128,128,0.1)"
    },
    yaxis: {
      title: "가격 (원)",
      showgrid: true,
      gridcolor: "rgba(128,128,128,0.2)",
      tickformat: ",.0f",
      side: "right"
    },
    title: {
      text: `${props.stock_name} (${props.stock_code})`,
      font: { size: 16 }
    },
    showlegend: true,
    legend: {
      x: 0,
      y: 1,
      xanchor: "left",
      yanchor: "top"
    },
    hovermode: "x unified"
  }

  const config = {
    displayModeBar: true,
    displaylogo: false,
    responsive: true
  }

  return (
    <div style={{ width: "100%" }}>
      <Plot
        data={plotData as any}
        layout={layout as any}
        config={config}
        style={{ width: "100%", height: "100%" }}
        useResizeHandler={true}
      />
    </div>
  )
}

export default RealtimeChart
