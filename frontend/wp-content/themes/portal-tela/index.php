<?php get_header(); ?>

<!-- Main Content -->
<section class="py-4 py-lg-5">
    <div class="container">
        
        <?php if (have_posts()) : ?>
        
            <!-- Header da seção -->
            <div class="d-flex align-items-center justify-content-between mb-4">
                <h2 class="h4 mb-0">
                    Últimas Notícias
                </h2>
                <span class="badge bg-light text-dark">
                    <?php 
                    global $wp_query;
                    echo $wp_query->found_posts; 
                    ?> notícias
                </span>
            </div>
            
            <div class="row g-4">
                <!-- Coluna Principal -->
                <div class="col-lg-8">
                    <?php 
                    $post_count = 0;
                    while (have_posts()) : the_post(); 
                        $post_count++;
                        
                        // Primeiro post em GRANDE destaque
                        if ($post_count === 1) :
                    ?>
                        <article class="featured-main mb-4 position-relative rounded-4 overflow-hidden shadow">
                            <?php if (has_post_thumbnail()) : ?>
                                <a href="<?php the_permalink(); ?>" class="d-block">
                                    <?php the_post_thumbnail('large', [
                                        'class' => 'w-100',
                                        'style' => 'aspect-ratio: 16/9; object-fit: cover;'
                                    ]); ?>
                                </a>
                            <?php else : ?>
                                <div class="bg-gradient-primary" style="aspect-ratio: 16/9; background: linear-gradient(135deg, var(--bs-primary), #0d47a1);"></div>
                            <?php endif; ?>
                            
                            <div class="featured-overlay position-absolute bottom-0 start-0 end-0 p-4 text-white" 
                                 style="background: linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.5) 50%, transparent 100%);">
                                <div class="mb-2">
                                    <?php
                                    $categories = get_the_category();
                                    if ($categories) :
                                    ?>
                                        <a href="<?php echo get_category_link($categories[0]->term_id); ?>" 
                                           class="badge bg-primary text-decoration-none">
                                            <?php echo esc_html($categories[0]->name); ?>
                                        </a>
                                    <?php endif; ?>
                                </div>
                                <h2 class="h3 mb-2">
                                    <a href="<?php the_permalink(); ?>" class="text-white text-decoration-none stretched-link">
                                        <?php the_title(); ?>
                                    </a>
                                </h2>
                                <p class="mb-2 opacity-75 d-none d-md-block">
                                    <?php echo wp_trim_words(get_the_excerpt(), 25); ?>
                                </p>
                                <div class="small opacity-75">
                                    <i class="bi bi-calendar3 me-1"></i>
                                    <?php echo get_the_date('d/m/Y'); ?>
                                    <span class="mx-2">•</span>
                                    <i class="bi bi-clock me-1"></i>
                                    <?php echo portal_reading_time(); ?> min de leitura
                                </div>
                            </div>
                        </article>
                        
                        <!-- Lista de posts abaixo do destaque -->
                        <div class="posts-list">
                            <h3 class="h6 text-muted text-uppercase mb-3">
                                <i class="bi bi-list-ul me-2"></i>Mais Notícias
                            </h3>
                        
                    <?php else : ?>
                        <!-- Posts em formato lista -->
                        <article class="post-item d-flex gap-3 mb-3 pb-3 border-bottom">
                            <?php if (has_post_thumbnail()) : ?>
                                <a href="<?php the_permalink(); ?>" class="flex-shrink-0">
                                    <?php the_post_thumbnail('thumbnail', [
                                        'class' => 'rounded',
                                        'style' => 'width: 120px; height: 80px; object-fit: cover;'
                                    ]); ?>
                                </a>
                            <?php else : ?>
                                <div class="flex-shrink-0 bg-light rounded d-flex align-items-center justify-content-center" 
                                     style="width: 120px; height: 80px;">
                                    <i class="bi bi-newspaper text-muted"></i>
                                </div>
                            <?php endif; ?>
                            
                            <div class="flex-grow-1 min-w-0">
                                <div class="mb-1">
                                    <?php
                                    $categories = get_the_category();
                                    if ($categories) :
                                    ?>
                                        <a href="<?php echo get_category_link($categories[0]->term_id); ?>" 
                                           class="badge bg-light text-dark text-decoration-none small">
                                            <?php echo esc_html($categories[0]->name); ?>
                                        </a>
                                    <?php endif; ?>
                                </div>
                                <h4 class="h6 mb-1 line-clamp-2">
                                    <a href="<?php the_permalink(); ?>" class="text-dark text-decoration-none hover-primary">
                                        <?php the_title(); ?>
                                    </a>
                                </h4>
                                <div class="text-muted small">
                                    <i class="bi bi-calendar3 me-1"></i>
                                    <?php echo get_the_date('d/m/Y'); ?>
                                    <span class="mx-1">•</span>
                                    <i class="bi bi-clock me-1"></i>
                                    <?php echo portal_reading_time(); ?> min
                                </div>
                            </div>
                        </article>
                    
                    <?php 
                        endif;
                    endwhile; 
                    ?>
                        </div><!-- /.posts-list -->
                </div>
                
                <!-- Sidebar -->
                <div class="col-lg-4">
                    <!-- Categorias -->
                    <div class="card border-0 shadow-sm mb-4">
                        <div class="card-header bg-primary text-white">
                            <h5 class="mb-0 h6">
                                <i class="bi bi-folder me-2"></i>Categorias
                            </h5>
                        </div>
                        <div class="card-body p-0">
                            <ul class="list-group list-group-flush">
                                <?php
                                $categories = get_categories(['number' => 8, 'orderby' => 'count', 'order' => 'DESC']);
                                foreach ($categories as $cat) :
                                ?>
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        <a href="<?php echo get_category_link($cat->term_id); ?>" 
                                           class="text-decoration-none text-dark">
                                            <?php echo esc_html($cat->name); ?>
                                        </a>
                                        <span class="badge bg-primary rounded-pill">
                                            <?php echo $cat->count; ?>
                                        </span>
                                    </li>
                                <?php endforeach; ?>
                            </ul>
                        </div>
                    </div>
                    
                    <!-- Tags populares -->
                    <?php
                    $tags = get_tags(['number' => 15, 'orderby' => 'count', 'order' => 'DESC']);
                    if ($tags) :
                    ?>
                    <div class="card border-0 shadow-sm">
                        <div class="card-header bg-dark text-white">
                            <h5 class="mb-0 h6">
                                <i class="bi bi-tags me-2"></i>Tags Populares
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="d-flex flex-wrap gap-2">
                                <?php foreach ($tags as $tag) : ?>
                                    <a href="<?php echo get_tag_link($tag->term_id); ?>" 
                                       class="badge bg-light text-dark text-decoration-none">
                                        <?php echo esc_html($tag->name); ?>
                                    </a>
                                <?php endforeach; ?>
                            </div>
                        </div>
                    </div>
                    <?php endif; ?>
                </div>
            </div>
            
            <!-- Paginação -->
            <nav class="mt-5" aria-label="Navegação de posts">
                <?php
                $pagination = paginate_links([
                    'type'      => 'array',
                    'prev_text' => '<i class="bi bi-chevron-left"></i> Anterior',
                    'next_text' => 'Próximo <i class="bi bi-chevron-right"></i>',
                ]);
                
                if ($pagination) :
                ?>
                    <ul class="pagination justify-content-center">
                        <?php foreach ($pagination as $page) : ?>
                            <li class="page-item <?php echo strpos($page, 'current') !== false ? 'active' : ''; ?>">
                                <?php echo str_replace('page-numbers', 'page-link', $page); ?>
                            </li>
                        <?php endforeach; ?>
                    </ul>
                <?php endif; ?>
            </nav>
        
        <?php else : ?>
            
            <!-- Nenhum post encontrado -->
            <div class="text-center py-5">
                <div class="mb-4">
                    <i class="bi bi-inbox display-1 text-muted"></i>
                </div>
                <h2 class="h4 text-muted mb-3">Nenhuma notícia publicada ainda</h2>
                <p class="text-muted mb-4">
                    As notícias aparecerão aqui assim que forem processadas e publicadas.
                </p>
                <div class="alert alert-info d-inline-block">
                    <i class="bi bi-info-circle me-2"></i>
                    Use o endpoint <code>/publish</code> da API para publicar notícias automaticamente.
                </div>
            </div>
            
        <?php endif; ?>
        
    </div>
</section>

<?php get_footer(); ?>