%% ============================================================
% Merge selected panels into one 3 x 3 figure
% New Figure:
% Mechanistic closure and satellite-observable precursor skill
%
% This script does NOT recompute events or read NetCDF.
% 
% and redraws selected panels with unified colors and labels.
%% ============================================================

clear; clc; close all;

%% ===================== 0. Paths =====================

rootDir = 'E:\GLORYS4V1';

matNM = fullfile(rootDir, ...
    'StepNM_near_miss_T100_onset_control', ...
    'StepNM_near_miss_T100_onset_control.mat');

matTD = fullfile(rootDir, ...
    'StepTD_thermocline_displacement_T100_estimate', ...
    'StepTD_thermocline_displacement_T100_estimate.mat');

matSK = fullfile(rootDir, ...
    'StepSK_DUACS_SLA_precursor_skill_AUC', ...
    'StepSK_DUACS_SLA_precursor_skill_AUC.mat');

outDir = fullfile(rootDir, ...
    'StepFIG_mechanistic_closure_satellite_precursor_skill');

if ~exist(outDir, 'dir')
    mkdir(outDir);
end

if ~exist(matNM, 'file')
    error('Cannot find near-miss MAT file:\n%s', matNM);
end

if ~exist(matTD, 'file')
    error('Cannot find thermocline-displacement MAT file:\n%s', matTD);
end

if ~exist(matSK, 'file')
    error('Cannot find DUACS skill MAT file:\n%s', matSK);
end

fprintf('Loading existing MAT outputs only...\n');
NM = load(matNM);
TD = load(matTD);
SK = load(matSK);

%% ===================== 1. Unified style =====================

plt = struct();

plt.fontName  = 'Arial';
plt.fontSize  = 16;
plt.lineWidth = 1.6;

% Required unified colors
cTrue = [0.82 0.16 0.13];   % True onset: red
cFail = [0.93 0.48 0.16];   % Failed P90 spell: orange
cNear = [0.10 0.43 0.78];   % Near-miss P85-P90: blue
cRand = [0.50 0.50 0.50];   % Random non-event: gray

cObs  = cTrue;              % Observed T100: red
cDisp = cNear;              % Displacement estimate: blue
cRes  = cRand;              % Residual: gray

cSLA  = cTrue;              % DUACS SLA: red
cT100 = cNear;              % T100 persistence: blue
cComb = [0.18 0.58 0.28];   % SLA + T100: green

GroupList = ["True onset", ...
             "Failed P90 spell", ...
             "Near-miss P85-P90", ...
             "Random non-event"];

GroupShort = {'True', 'Failed P90', 'Near-miss', 'Random'};

GroupColors = [cTrue; cFail; cNear; cRand];

colors = containers.Map;
colors("True onset")        = cTrue;
colors("Failed P90 spell")  = cFail;
colors("Near-miss P85-P90") = cNear;
colors("Random non-event")  = cRand;

%% ===================== 2. Basic checks =====================

needNM = {'PreEvent','ProbTab'};
for i = 1:numel(needNM)
    if ~isfield(NM, needNM{i})
        error('Near-miss MAT does not contain %s.', needNM{i});
    end
end

needTD = {'D','Comp','Metrics','PreEvent'};
for i = 1:numel(needTD)
    if ~isfield(TD, needTD{i})
        error('Thermocline MAT does not contain %s.', needTD{i});
    end
end

needSK = {'Cand','Skill','ProbSLA','ROCstore'};
for i = 1:numel(needSK)
    if ~isfield(SK, needSK{i})
        error('DUACS skill MAT does not contain %s.', needSK{i});
    end
end

NM.PreEvent = local_string_col(NM.PreEvent, 'Group');
NM.ProbTab  = local_string_col(NM.ProbTab,  'Predictor');

TD.Comp     = local_string_col(TD.Comp,     'Variable');
TD.Metrics  = local_string_col(TD.Metrics,  'Sample');

SK.Cand     = local_string_col(SK.Cand,     'Group');
SK.Skill    = local_string_col(SK.Skill,    'Comparison');
SK.Skill    = local_string_col(SK.Skill,    'Predictor');
SK.Skill    = local_string_col(SK.Skill,    'PredictorLabel');

%% ===================== 3. Create 3 x 3 figure =====================

fig = figure('Color','w', 'Position',[40 40 1850 1500]);
set(fig, 'Renderer','painters');

tl = tiledlayout(fig, 3, 3, ...
    'Padding','compact', ...
    'TileSpacing','compact');

%% ============================================================
% (a) near-miss Fig d
% Pre-onset SSH/D26/T100 anomalies bar
%% ============================================================

ax = nexttile(tl, 1);
hold(ax,'on'); box(ax,'on'); grid(ax,'on');

PE = NM.PreEvent;

metricNames  = ["SSH_pre_z", "D26_pre_z", "T100_pre_z"];
metricLabels = {'SSH', 'D26', 'T100'};

B   = nan(numel(metricNames), numel(GroupList));
SEM = nan(numel(metricNames), numel(GroupList));

for im = 1:numel(metricNames)
    v = metricNames(im);

    if ~ismember(v, PE.Properties.VariableNames)
        warning('NM.PreEvent does not contain %s. Panel (a) may be incomplete.', v);
        continue;
    end

    for ig = 1:numel(GroupList)
        idx = PE.Group == GroupList(ig);
        x = PE.(v)(idx);
        x = x(isfinite(x));

        B(im,ig) = mean(x, 'omitnan');

        if numel(x) > 1
            SEM(im,ig) = std(x, 0, 'omitnan') ./ sqrt(numel(x));
        end
    end
end

bh = bar(ax, B, 'grouped', ...
    'EdgeColor',[0.25 0.25 0.25], ...
    'LineWidth',0.6);

for ig = 1:numel(GroupList)
    bh(ig).FaceColor = GroupColors(ig,:);
    bh(ig).DisplayName = GroupList(ig);
end

for ig = 1:numel(GroupList)
    try
        errorbar(ax, bh(ig).XEndPoints, B(:,ig), SEM(:,ig), ...
            'k.', 'LineWidth',0.8, 'CapSize',5, ...
            'HandleVisibility','off');
    catch
    end
end

yline(ax, 0, 'k:', 'HandleVisibility','off');

set(ax, 'XTick', 1:numel(metricLabels), ...
    'XTickLabel', metricLabels);

ylabel(ax, 'Mean z anomaly, day -10 to -1');
title(ax, '(a) Pre-onset SSH / D26 / T100 anomalies');

legend(ax, bh, cellstr(GroupList), ...
    'Location','northeast', ...
    'Box','off');

local_style_axis(ax, plt);

%% ============================================================
% (b) near-miss Fig f
% True-onset fraction by SSH-D26 precursor quartile
%% ============================================================

ax = nexttile(tl, 2);
hold(ax,'on'); box(ax,'on'); grid(ax,'on');

P = NM.ProbTab;

if ~isempty(P) && height(P) > 0
    bar(ax, P.Quartile, P.TrueOnsetFraction, 0.65, ...
        'FaceColor', cNear, ...
        'EdgeColor',[0.25 0.25 0.25], ...
        'LineWidth',0.7);

    ylim(ax, [0 1]);
    xlim(ax, [0.4 4.6]);
    set(ax, 'XTick', 1:4);

    xlabel(ax, 'SSH-D26 precursor quartile');
    ylabel(ax, 'Fraction of true onsets');
else
    text(ax, 0.5, 0.5, 'Not enough samples', ...
        'Units','normalized', ...
        'HorizontalAlignment','center');
end

title(ax, '(b) True-onset fraction by precursor strength');
local_style_axis(ax, plt);

%% ============================================================
% (c) thermocline Fig c
% Observed vs displacement-estimated daily T100
%% ============================================================

ax = nexttile(tl, 3);
hold(ax,'on'); box(ax,'on'); grid(ax,'on');

D = TD.D;

ok = isfinite(D.T100_anom_obs) & isfinite(D.T100_disp_est);

scatter(ax, D.T100_anom_obs(ok), D.T100_disp_est(ok), 9, ...
    'MarkerFaceColor',[0.25 0.25 0.25], ...
    'MarkerEdgeColor','none', ...
    'MarkerFaceAlpha',0.22);

if ismember('IsEventDay_final', D.Properties.VariableNames)
    okE = ok & logical(D.IsEventDay_final);
else
    okE = false(size(ok));
end

scatter(ax, D.T100_anom_obs(okE), D.T100_disp_est(okE), 14, ...
    'MarkerFaceColor', cTrue, ...
    'MarkerEdgeColor','none', ...
    'MarkerFaceAlpha',0.42);

mAll = local_get_metric_row(TD.Metrics, "All days");

local_add_saved_scatter_lines(ax, ...
    D.T100_anom_obs(ok), ...
    D.T100_disp_est(ok), ...
    mAll);

xlabel(ax, 'Observed T100 anomaly (^{\circ}C)');
ylabel(ax, 'Displacement-estimated T100 anomaly (^{\circ}C)');
title(ax, '(c) Observed vs displacement-estimated daily T100');

if ~isempty(mAll)
    txt = sprintf('r = %.2f\nR^2 = %.2f', ...
        mAll.R(1), mAll.R2_corr(1));

    text(ax, 0.05, 0.94, txt, ...
        'Units','normalized', ...
        'HorizontalAlignment','left', ...
        'VerticalAlignment','top', ...
        'BackgroundColor','w', ...
        'Margin',4, ...
        'FontName',plt.fontName, ...
        'FontSize',plt.fontSize - 0.5);
end

local_style_axis(ax, plt);

%% ============================================================
% (d) thermocline Fig d
% Event-onset composite: observed / displacement / residual
%% ============================================================

ax = nexttile(tl, 4);
hold(ax,'on'); box(ax,'on'); grid(ax,'on');

local_plot_comp(ax, TD.Comp, "T100_anom_obs",  cObs,  plt.lineWidth, 'Observed T100');
local_plot_comp(ax, TD.Comp, "T100_disp_est",  cDisp, plt.lineWidth, 'Displacement estimate');
local_plot_comp(ax, TD.Comp, "T100_residual",  cRes,  1.25,          'Residual');

xline(ax, 0, 'k--', 'HandleVisibility','off');
yline(ax, 0, 'k:',  'HandleVisibility','off');

xlabel(ax, 'Days relative to T100 event onset');
ylabel(ax, 'T100 anomaly (^{\circ}C)');
title(ax, '(d) Event-onset composite');

legend(ax, 'Location','northwest', 'Box','off');

local_style_axis(ax, plt);

%% ============================================================
% (e) thermocline Fig f
% Pre-onset mean decomposition
%% ============================================================

ax = nexttile(tl, 5);
hold(ax,'on'); box(ax,'on'); grid(ax,'on');

PEtd = TD.PreEvent;

preMeanObs = mean(PEtd.T100_obs_pre,   'omitnan');
preMeanEst = mean(PEtd.T100_disp_pre,  'omitnan');
preMeanRes = mean(PEtd.T100_resid_pre, 'omitnan');

B = [preMeanObs, preMeanEst, preMeanRes];

b = bar(ax, B, 0.6, ...
    'FaceColor','flat', ...
    'EdgeColor',[0.25 0.25 0.25], ...
    'LineWidth',0.8);

b.CData = [cObs; cDisp; cRes];

set(ax, 'XTick', 1:3, ...
    'XTickLabel', {'Observed','Displacement','Residual'});

ylabel(ax, 'Mean T100 anomaly, day -10 to -1 (^{\circ}C)');
title(ax, '(e) Pre-onset mean decomposition');

yline(ax, 0, 'k:', 'HandleVisibility','off');

for i = 1:3
    if isfinite(B(i))
        if B(i) >= 0
            va = 'bottom';
            ytxt = B(i) + 0.02;
        else
            va = 'top';
            ytxt = B(i) - 0.02;
        end

        text(ax, i, ytxt, sprintf('%.2f', B(i)), ...
            'HorizontalAlignment','center', ...
            'VerticalAlignment',va, ...
            'FontName',plt.fontName, ...
            'FontSize',plt.fontSize - 0.5);
    end
end

if isfinite(preMeanObs) && abs(preMeanObs) > 1e-6
    fracText = sprintf('Displacement / observed = %.0f%%', ...
        100 * preMeanEst ./ preMeanObs);
else
    fracText = 'Displacement / observed = NaN';
end

text(ax, 0.99, 0.94, fracText, ...
    'Units','normalized', ...
    'HorizontalAlignment','right', ...
    'VerticalAlignment','top', ...
    'BackgroundColor','w', ...
    'Margin',4, ...
    'FontName',plt.fontName, ...
    'FontSize',plt.fontSize - 0.5);

local_style_axis(ax, plt);

%% ============================================================
% (f) DUACS skill Fig b
% Pre-onset DUACS SLA bar
%% ============================================================

ax = nexttile(tl, 6);
hold(ax,'on'); box(ax,'on'); grid(ax,'on');

Cand = SK.Cand;

B   = nan(numel(GroupList),1);
SEM = nan(numel(GroupList),1);

for ig = 1:numel(GroupList)
    idx = Cand.Group == GroupList(ig);

    if ~ismember('DUACS_SLA_pre_z', Cand.Properties.VariableNames)
        error('SK.Cand does not contain DUACS_SLA_pre_z.');
    end

    x = Cand.DUACS_SLA_pre_z(idx);
    x = x(isfinite(x));

    B(ig) = mean(x, 'omitnan');

    if numel(x) > 1
        SEM(ig) = std(x, 0, 'omitnan') ./ sqrt(numel(x));
    end
end

b = bar(ax, B, 0.68, ...
    'FaceColor','flat', ...
    'EdgeColor',[0.25 0.25 0.25], ...
    'LineWidth',0.7);

b.CData = GroupColors;

errorbar(ax, 1:numel(B), B, SEM, ...
    'k.', 'LineWidth',0.9, 'CapSize',6);

yline(ax, 0, 'k:', 'HandleVisibility','off');

set(ax, 'XTick', 1:numel(GroupList), ...
    'XTickLabel', GroupShort, ...
    'XTickLabelRotation',20);

ylabel(ax, 'Mean DUACS SLA z, day -10 to -1');
title(ax, '(f) Pre-onset DUACS SLA');

local_style_axis(ax, plt);

%% ============================================================
% (g) DUACS skill Fig c
% ROC: true onset vs warm near-miss
%% ============================================================

ax = nexttile(tl, 7);
hold(ax,'on'); box(ax,'on'); grid(ax,'on');

plot(ax, [0 1], [0 1], 'k--', ...
    'LineWidth',0.9, ...
    'HandleVisibility','off');

rocPreds  = ["DUACS_SLA_pre_z", "T100_pre_z", "SLA_T100_score"];
rocLabels = ["DUACS SLA", "T100", "SLA + T100"];
rocColors = [cSLA; cT100; cComb];

for ip = 1:numel(rocPreds)

    key = matlab.lang.makeValidName("True vs warm near-miss_" + rocPreds(ip));

    if ~isfield(SK.ROCstore, key)
        warning('ROCstore does not contain key: %s', key);
        continue;
    end

    R = SK.ROCstore.(key);

    plot(ax, R.FPR, R.TPR, '-', ...
        'Color', rocColors(ip,:), ...
        'LineWidth', plt.lineWidth, ...
        'DisplayName', sprintf('%s AUC=%.2f', rocLabels(ip), R.AUC));
end

xlabel(ax, 'False positive rate');
ylabel(ax, 'True positive rate');
title(ax, '(g) ROC: true onset vs warm near-miss');

xlim(ax, [0 1]);
ylim(ax, [0 1]);

legend(ax, 'Location','southeast', 'Box','off');

local_style_axis(ax, plt);

%% ============================================================
% (h) DUACS skill Fig d
% AUC bar
%% ============================================================

ax = nexttile(tl, 8);
hold(ax,'on'); box(ax,'on'); grid(ax,'on');

Skill = SK.Skill;

plotComp  = "True vs warm near-miss";
plotPreds = ["DUACS_SLA_pre_z", "T100_pre_z", "SLA_T100_score"];
plotLabs  = {'DUACS SLA', 'T100', 'SLA+T100'};
plotCols  = [cSLA; cT100; cComb];

AUCvals = nan(numel(plotPreds),1);
CIlo    = nan(numel(plotPreds),1);
CIhi    = nan(numel(plotPreds),1);

for ip = 1:numel(plotPreds)
    idx = Skill.Comparison == plotComp & ...
          Skill.Predictor   == plotPreds(ip);

    if any(idx)
        ii = find(idx,1);
        AUCvals(ip) = Skill.AUC(ii);

        if ismember('AUC_CI_low', Skill.Properties.VariableNames)
            CIlo(ip) = Skill.AUC_CI_low(ii);
        end

        if ismember('AUC_CI_high', Skill.Properties.VariableNames)
            CIhi(ip) = Skill.AUC_CI_high(ii);
        end
    else
        warning('Cannot find AUC row for %s.', plotPreds(ip));
    end
end

b = bar(ax, AUCvals, 0.66, ...
    'FaceColor','flat', ...
    'EdgeColor',[0.25 0.25 0.25], ...
    'LineWidth',0.7);

b.CData = plotCols;

errLow  = AUCvals - CIlo;
errHigh = CIhi - AUCvals;

errorbar(ax, 1:numel(AUCvals), AUCvals, errLow, errHigh, ...
    'k.', 'LineWidth',1.0, 'CapSize',6);

yline(ax, 0.5, 'k--', 'HandleVisibility','off');

set(ax, 'XTick', 1:numel(plotPreds), ...
    'XTickLabel', plotLabs, ...
    'XTickLabelRotation',15);

ylabel(ax, 'AUC');
title(ax, '(h) AUC against warm near-miss controls');

ylim(ax, [0.3 1.0]);

for ip = 1:numel(AUCvals)
    if isfinite(AUCvals(ip))
        text(ax, ip, AUCvals(ip)+0.035, sprintf('%.2f', AUCvals(ip)), ...
            'HorizontalAlignment','center', ...
            'FontName',plt.fontName, ...
            'FontSize',plt.fontSize - 0.5);
    end
end

local_style_axis(ax, plt);

%% ============================================================
% (i) DUACS skill Fig f
% True-onset fraction by DUACS SLA quartile
%% ============================================================

ax = nexttile(tl, 9);
hold(ax,'on'); box(ax,'on'); grid(ax,'on');

ProbSLA = SK.ProbSLA;

if ~isempty(ProbSLA) && height(ProbSLA) > 0
    bar(ax, ProbSLA.Quartile, ProbSLA.TrueOnsetFraction, 0.65, ...
        'FaceColor', cSLA, ...
        'EdgeColor',[0.25 0.25 0.25], ...
        'LineWidth',0.7);

    ylim(ax, [0 1]);
    xlim(ax, [0.4 4.6]);
    set(ax, 'XTick', 1:4);

    xlabel(ax, 'DUACS SLA precursor quartile');
    ylabel(ax, 'Fraction of true onsets');
else
    text(ax, 0.5, 0.5, 'Not enough samples', ...
        'Units','normalized', ...
        'HorizontalAlignment','center');
end

title(ax, '(i) True-onset fraction by DUACS SLA');

local_style_axis(ax, plt);

%% ===================== 4. Figure title and export =====================

% sgtitle(tl, ...
%     'Mechanistic closure and satellite-observable precursor skill', ...
%     'FontName',plt.fontName, ...
%     'FontSize',18, ...
%     'FontWeight','bold');

% Hide axes toolbar
allAxes = findall(fig, 'Type','axes');
for ia = 1:numel(allAxes)
    try
        allAxes(ia).Toolbar.Visible = 'off';
    catch
    end
end

outPNG = fullfile(outDir, ...
    'Fig_mechanistic_closure_satellite_precursor_skill_3x3.png');
outTIF = fullfile(outDir, ...
    'Fig_mechanistic_closure_satellite_precursor_skill_3x3.tif');
outPDF = fullfile(outDir, ...
    'Fig_mechanistic_closure_satellite_precursor_skill_3x3.pdf');

exportgraphics(fig, outPNG, 'Resolution',600);
exportgraphics(fig, outTIF, 'Resolution',600);
exportgraphics(fig, outPDF, 'ContentType','vector');

fprintf('\nSaved merged 3 x 3 figure:\n');
fprintf('1) %s\n', outPNG);
fprintf('2) %s\n', outTIF);
fprintf('3) %s\n', outPDF);

fprintf('\nFinished.\n');

%% ========================================================================
% Local functions
%% ========================================================================

function T = local_string_col(T, colName)

    if istable(T) && ismember(colName, T.Properties.VariableNames)
        T.(colName) = string(T.(colName));
    end

end


function local_style_axis(ax, plt)

    set(ax, ...
        'FontName', plt.fontName, ...
        'FontSize', plt.fontSize, ...
        'LineWidth', 0.9, ...
        'TickDir', 'out', ...
        'Box', 'on', ...
        'Layer', 'top');

    grid(ax, 'on');
    ax.GridAlpha = 0.18;
    ax.MinorGridAlpha = 0.10;

end


function mRow = local_get_metric_row(Metrics, sampleName)

    mRow = table();

    if ~istable(Metrics)
        return;
    end

    if ~ismember('Sample', Metrics.Properties.VariableNames)
        return;
    end

    Metrics.Sample = string(Metrics.Sample);

    idx = Metrics.Sample == string(sampleName);

    if any(idx)
        mRow = Metrics(find(idx,1), :);
    end

end


function local_add_saved_scatter_lines(ax, x, y, mRow)

    x = x(:);
    y = y(:);

    ok = isfinite(x) & isfinite(y);

    if sum(ok) < 3
        return;
    end

    allv = [x(ok); y(ok)];
    mn = min(allv, [], 'omitnan');
    mx = max(allv, [], 'omitnan');

    pad = 0.08 * (mx - mn);

    if ~isfinite(pad) || pad == 0
        pad = 0.1;
    end

    lims = [mn-pad, mx+pad];

    plot(ax, lims, lims, 'k--', ...
        'LineWidth',0.9, ...
        'HandleVisibility','off');

    % Use saved regression slope/intercept from Metrics when available.
    if ~isempty(mRow) && ...
       ismember('Slope_est_vs_obs', mRow.Properties.VariableNames) && ...
       ismember('Intercept_est_vs_obs', mRow.Properties.VariableNames)

        slope = mRow.Slope_est_vs_obs(1);
        intercept = mRow.Intercept_est_vs_obs(1);

        if isfinite(slope) && isfinite(intercept)
            xx = linspace(lims(1), lims(2), 100);
            yy = slope .* xx + intercept;

            plot(ax, xx, yy, '-', ...
                'Color',[0.10 0.10 0.10], ...
                'LineWidth',1.1, ...
                'HandleVisibility','off');
        end
    end

    xlim(ax, lims);
    ylim(ax, lims);

end


function local_plot_comp(ax, Comp, varName, colorVal, lineWidth, displayName)

    if ~istable(Comp)
        warning('Comp is not a table.');
        return;
    end

    needCols = {'Variable','RelDay','Mean','SEM'};

    for i = 1:numel(needCols)
        if ~ismember(needCols{i}, Comp.Properties.VariableNames)
            warning('Comp does not contain %s.', needCols{i});
            return;
        end
    end

    Comp.Variable = string(Comp.Variable);

    idx = Comp.Variable == string(varName);
    T = Comp(idx, :);

    if isempty(T)
        warning('Cannot find composite variable: %s', varName);
        return;
    end

    T = sortrows(T, 'RelDay');

    xx = T.RelDay;
    yy = T.Mean;
    ee = T.SEM;

    fill(ax, [xx; flipud(xx)], ...
        [yy-ee; flipud(yy+ee)], ...
        colorVal, ...
        'FaceAlpha',0.13, ...
        'EdgeColor','none', ...
        'HandleVisibility','off');

    plot(ax, xx, yy, '-', ...
        'Color', colorVal, ...
        'LineWidth', lineWidth, ...
        'DisplayName', displayName);

    xlim(ax, [min(xx) max(xx)]);

end