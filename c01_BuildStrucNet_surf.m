clc; clear;

%% INPUTS
CATROOT = '#{CATROOT}#';
GIFTIROOT = '#{GIFTIROOT}#';
ATLASNAME = '#{ATLASNAME}#';
FILENAME = '#{FILENAME}#';
OUTPREFIX = '#{OUTPREFIX}#';
% NCORE = #{NCORE}#;

%% INPUTS
% CATROOT = '~/Documents/MATLAB/toolbox/spm12/toolbox/cat12';
% GIFTIROOT = 'Resource/gifti-master';
% ATLASNAME = 'Resource/atlases_surfaces/lh.Schaefer2018_400Parcels_7Networks_order.annot';
% FILENAME = 'Derivation/test-buildnet/sub-99156/anat/surf/s20.mesh.depth.resampled.sub-99156_T1w.gii';
% OUTPREFIX = 'Derivation/test-buildnet/sub-99156/s20.mesh.depth.resampled.sub-99156_T1w';
% NCORE = 4;

%%
NUMSAMPLE = 2^8;
addpath(GIFTIROOT);

lhannotname = ATLASNAME;
[lhvertices, lhlabel, lhcolortable] = read_annotation(lhannotname);
rhannotname = strrep(lhannotname, 'lh.', 'rh.');
[rhvertices, rhlabel, rhcolortable] = read_annotation(rhannotname);

% label of unknown
labels_unknow = 1639705;
prefix_label = 100000000;
% labels = [lhlabel + prefix_label; rhlabel + 2 * prefix_label];
labels = [lhlabel; rhlabel];
% uni_labels = labels;
% uni_labels = unique([lhcolortable.table(:, 5) + prefix_label; rhcolortable.table(:, 5) + 2 * prefix_label]);
% for bna atlas
uni_labels = unique(lhcolortable.table(:, 5));
uni_labels(uni_labels == labels_unknow) = [];
% uni_labels(uni_labels == labels_unknow + prefix_label) = [];
% uni_labels(uni_labels == labels_unknow + 2 * prefix_label) = [];
% uni_labels(uni_labels == 1644825 + prefix_label) = [];
% uni_labels(uni_labels == 1644825 + 2 * prefix_label) = [];

filename = FILENAME;
gii = gifti(filename);

num_rois = size(uni_labels);
num_rois = num_rois(1);

mat_kl = ones(1, num_rois * num_rois);
mat_js = mat_kl;

%% build network
[index_a, index_b] = meshgrid(1:num_rois, 1:num_rois);

for i = 1:numel(index_a)
    if index_a(i) >= index_b(i)
        continue
    end
    p_index = index_a(i);
    q_index = index_b(i);
    
    p_label = uni_labels(p_index);
    q_label = uni_labels(q_index);
    [pf, px] = ksdensity(gii.cdata(labels == p_label), 'Function', 'pdf', 'NumPoints', NUMSAMPLE);
    [qf, qx] = ksdensity(gii.cdata(labels == q_label), 'Function', 'pdf', 'NumPoints', NUMSAMPLE);

    % normalize
    pf = pf ./ sum(pf);
    qf = qf ./ sum(qf);

    klds = exp(-1 * (KLD(pf, qf) + KLD(qf, pf)));
    jsds = 1 - sqrt(JSD(pf, qf));

    mat_kl(i) = klds;
    mat_js(i) = jsds;
end

mat_kl = reshape(mat_kl, num_rois, num_rois);
mat_kl = mat_kl + mat_kl' - 1;
mat_js = reshape(mat_js, num_rois, num_rois);
mat_js = mat_js + mat_js' - 1;


%% save labels
str_label = zeros([num_rois, 1]);
str_name = strings(num_rois, 1);
str_hemi = '_lh';
for i = 1:num_rois
    l = uni_labels(i);
        
    % if ismember(l, lhlabel)
    % true_index = mod(l, prefix_label);
    % if fix(l / prefix_label) == 1
    %     str_hemi = '_lh';
    %     true_name = lhcolortable.struct_names(lhcolortable.table(:, 5) == true_index);
    % else
    %     str_hemi = '_rh';
    %     true_name = rhcolortable.struct_names(rhcolortable.table(:, 5) == true_index);
    % end
    true_index = l;
    true_name = lhcolortable.struct_names(lhcolortable.table(:, 5) == true_index);
    str_label(i) = true_index;
    % str_name(i) = {strcat(true_name{1}, str_hemi)};
    str_name(i) = {true_name{1}};
end

%% save results
str_table = table(str_label, str_name, 'VariableNames', {'Label', 'Name'});
writetable(str_table, strcat(OUTPREFIX, '.csv'));
writematrix(mat_kl, strcat(OUTPREFIX, '_net-kl.txt'), 'Delimiter', '\t');
writematrix(mat_js, strcat(OUTPREFIX, '_net-js.txt'), 'Delimiter', '\t');

%% save figures
% save(gii, 'mesh.gii');
% cat_surf_display(struct('data', 'mesh.gii', 'usefsaverage', 1, 'multisurf', 1, 'dpi', 1500, 'caxis', [0, 3], 'colormap', 'autumn'))

disp('Done.');

%% function
function val = JSD(p, q)
tmp1 = log2(p ./ ((p + q) ./ 2)) .* p;
val1 = sum(tmp1(isfinite(tmp1)), 'omitnan');
tmp2 = log2(q ./ ((q + p) ./ 2)) .* q;
val2 = sum(tmp2(isfinite(tmp2)), 'omitnan');
val = (val1 + val2) / 2;
end

function val = KLD(p, q)
tmp = log(p ./ q) .* p;
val = sum(tmp(isfinite(tmp)), 'omitnan');
end
%% function end