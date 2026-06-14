import { useState } from 'react'
import axios from 'axios'
import { MOCK_DATA } from '../data/mockData'

const API_URL = 'http://localhost:8000'

export function useAnalysis() {
  const [state, setState] = useState({
    status: 'idle',
    currentAgentIndex: -1,
    agentStatuses: {},
    result: null,
    error: null,
    usingMock: false,
  })

  const reset = () => {
    setState({
      status: 'idle', currentAgentIndex: -1,
      agentStatuses: {}, result: null, error: null, usingMock: false,
    })
  }

  const run = async (caseDescription, judgeName = '') => {
    const agentKeys = ['precedent', 'argument', 'outcome', 'judge']

    setState(s => ({
      ...s, status: 'running', currentAgentIndex: 0,
      agentStatuses: { precedent: 'running', argument: 'pending', outcome: 'pending', judge: 'pending' },
      result: null, error: null,
    }))

    const backendCall = axios.post(
      `${API_URL}/analyse`,
      { case_description: caseDescription, judge_name: judgeName },
      { timeout: 120000 }
    ).catch(err => {
      console.warn('Backend unavailable:', err.message)
      return null
    })

    const AGENT_DURATION = 2600
    for (let i = 0; i < agentKeys.length; i++) {
      setState(s => ({
        ...s,
        currentAgentIndex: i,
        agentStatuses: Object.fromEntries(
          agentKeys.map((k, j) => [k, j < i ? 'done' : j === i ? 'running' : 'pending'])
        ),
      }))
      await sleep(AGENT_DURATION)
    }

    const res = await backendCall
    const usingMock = !res?.data
    const result = res?.data || { ...MOCK_DATA, case_description: caseDescription, judge_name: judgeName }

    setState(s => ({
      ...s, status: 'done',
      agentStatuses: { precedent: 'done', argument: 'done', outcome: 'done', judge: 'done' },
      currentAgentIndex: 3,
      result,
      usingMock,
    }))

    return result
  }

  return { state, run, reset }
}

const sleep = ms => new Promise(r => setTimeout(r, ms))