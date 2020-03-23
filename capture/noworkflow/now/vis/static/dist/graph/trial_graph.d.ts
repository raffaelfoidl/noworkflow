import { Selection as d3_Selection, BaseType as d3_BaseType } from 'd3-selection';
import { Widget } from '@phosphor/widgets';
import { BaseActivationGraphWidget } from './base_activation_graph';
import { TrialGraph, TrialGraphData } from '@noworkflow/trial';
export declare class TrialGraphWidget extends BaseActivationGraphWidget {
    name: string;
    cls: string;
    t1: number;
    t2: number;
    graph: TrialGraph;
    d3node: d3_Selection<d3_BaseType, {}, HTMLElement | null, any>;
    static url(trialId: number, selectedGraph: string, useCache: boolean): string;
    constructor(name: string, cls: string, t1: number, t2: number);
    setGraph(data: TrialGraphData, config?: any): void;
    configureGraph(selectedGraph: string | undefined, useCache: boolean | undefined, data: TrialGraphData): void;
    load(selectedGraph?: string, useCache?: boolean): void;
    protected onResize(msg: Widget.ResizeMessage): void;
}
