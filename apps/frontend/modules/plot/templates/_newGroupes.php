<div id="overDiv"></div>
<?php $PictureID = "Map_".rand(1,10000).".map"; ?>
<?php if ($type === "home") echo '<a href="'.url_for('@top_global').'">'; ?>
<img id="graph_groupes" alt="Répartition de l'activité parlementaire sur les 12 derniers mois" src="<?php echo url_for('@groupes_plot_graph?type='.$type.'&mapId='.$PictureID); ?>" OnMouseMove="getMousePosition(event);" OnMouseOut="nd();"/>
<?php if ($type === "home") echo '</a>'; ?>
<script> LoadImageMap("graph_groupes", "<?php echo url_for('@groupes_plot_graph?type='.$type.'&drawAction=map&mapId='.$PictureID); ?>"); </script>
<?php echo include_partial('plot/groupesLegende', array()); ?>
