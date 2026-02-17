<?php get_header(); ?>

<!-- Archive Header -->
<header class="archive-header bg-light py-5 border-bottom">
    <div class="container">
        <div class="row">
            <div class="col-lg-8">
                <?php if (is_category()) : ?>
                    <span class="badge bg-primary mb-3">Categoria</span>
                    <h1 class="display-5 fw-bold mb-2"><?php single_cat_title(); ?></h1>
                    <?php if (category_description()) : ?>
                        <p class="lead text-muted mb-0"><?php echo category_description(); ?></p>
                    <?php endif; ?>
                
                <?php elseif (is_tag()) : ?>
                    <span class="badge bg-secondary mb-3">Tag</span>
                    <h1 class="display-5 fw-bold mb-2"><?php single_tag_title(); ?></h1>
                    <?php if (tag_description()) : ?>
                        <p class="lead text-muted mb-0"><?php echo tag_description(); ?></p>
                    <?php endif; ?>
                
                <?php elseif (is_author()) : ?>
                    <span class="badge bg-info mb-3">Autor</span>
                    <h1 class="display-5 fw-bold mb-2"><?php the_author(); ?></h1>
                    <?php if (get_the_author_meta('description')) : ?>
                        <p class="lead text-muted mb-0"><?php the_author_meta('description'); ?></p>
                    <?php endif; ?>
                
                <?php elseif (is_date()) : ?>
                    <span class="badge bg-dark mb-3">Arquivo</span>
                    <h1 class="display-5 fw-bold mb-2">
                        <?php
                        if (is_day()) {
                            echo get_the_date('d \d\e F \d\e Y');
                        } elseif (is_month()) {
                            echo get_the_date('F \d\e Y');
                        } elseif (is_year()) {
                            echo get_the_date('Y');
                        }
                        ?>
                    </h1>
                
                <?php elseif (is_search()) : ?>
                    <span class="badge bg-warning text-dark mb-3">Busca</span>
                    <h1 class="display-5 fw-bold mb-2">
                        Resultados para: "<?php echo get_search_query(); ?>"
                    </h1>
                    <p class="lead text-muted mb-0">
                        <?php 
                        global $wp_query;
                        printf('%d resultado(s) encontrado(s)', $wp_query->found_posts);
                        ?>
                    </p>
                
                <?php else : ?>
                    <h1 class="display-5 fw-bold mb-2"><?php the_archive_title(); ?></h1>
                    <?php the_archive_description('<p class="lead text-muted mb-0">', '</p>'); ?>
                
                <?php endif; ?>
            </div>
        </div>
    </div>
</header>

<!-- Archive Content -->
<section class="py-5">
    <div class="container">
        
        <?php if (have_posts()) : ?>
        
            <div class="row g-4">
                <?php while (have_posts()) : the_post(); ?>
                    <div class="col-md-6 col-lg-4">
                        <article class="card h-100 border-0 shadow-sm hover-lift">
                            <?php if (has_post_thumbnail()) : ?>
                                <a href="<?php the_permalink(); ?>">
                                    <?php the_post_thumbnail('medium', [
                                        'class' => 'card-img-top',
                                        'style' => 'aspect-ratio: 16/10; object-fit: cover;'
                                    ]); ?>
                                </a>
                            <?php endif; ?>
                            
                            <div class="card-body d-flex flex-column">
                                <?php if (!is_category()) : ?>
                                    <div class="mb-2">
                                        <?php
                                        $categories = get_the_category();
                                        if ($categories) :
                                        ?>
                                            <a href="<?php echo get_category_link($categories[0]->term_id); ?>" 
                                               class="badge bg-primary text-decoration-none small">
                                                <?php echo esc_html($categories[0]->name); ?>
                                            </a>
                                        <?php endif; ?>
                                    </div>
                                <?php endif; ?>
                                
                                <h2 class="card-title h5 mb-2">
                                    <a href="<?php the_permalink(); ?>" class="text-decoration-none text-dark stretched-link">
                                        <?php the_title(); ?>
                                    </a>
                                </h2>
                                
                                <p class="card-text text-muted small flex-grow-1">
                                    <?php echo wp_trim_words(get_the_excerpt(), 15); ?>
                                </p>
                                
                                <div class="text-muted small mt-auto pt-2 border-top">
                                    <i class="bi bi-calendar3 me-1"></i>
                                    <?php echo get_the_date('d/m/Y'); ?>
                                    <span class="mx-2">&bull;</span>
                                    <i class="bi bi-clock me-1"></i>
                                    <?php echo portal_reading_time(); ?> min
                                </div>
                            </div>
                        </article>
                    </div>
                <?php endwhile; ?>
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
            
            <div class="text-center py-5">
                <i class="bi bi-search display-1 text-muted mb-4"></i>
                <h2 class="h4 text-muted">Nenhum resultado encontrado</h2>
                <p class="text-muted">Tente uma nova busca ou navegue pelas categorias.</p>
                <a href="<?php echo home_url('/'); ?>" class="btn btn-primary">
                    <i class="bi bi-house me-2"></i>Voltar ao início
                </a>
            </div>
            
        <?php endif; ?>
        
    </div>
</section>

<?php get_footer(); ?>
