import tensorflow as tf


def euclidean_squared(A, B):
    """
    Returns euclidean distance between two batches of shape [B,N,F] and [B,M,F] where B is batch size, N is number of
    examples in the batch of first set, M is number of examples in the batch of second set, F is number of spatial
    features.

    Returns:
    A matrix of size [B, N, M] where each element [i,j] denotes euclidean distance between ith entry in first set and
    jth in second set.

    """

    shape_A = A.get_shape().as_list()
    shape_B = B.get_shape().as_list()
    
    assert (A.dtype == tf.float32 or A.dtype == tf.float64) and (B.dtype == tf.float32 or B.dtype == tf.float64)
    assert len(shape_A) == 3 and len(shape_B) == 3
    assert shape_A[0] == shape_B[0] and shape_A[1] == shape_B[1]
    
    #just exploit broadcasting
    B_trans = tf.transpose(tf.expand_dims(B,axis=3), perm=[0, 3, 1, 2])
    A_exp = tf.expand_dims(A,axis=2)
    diff = A_exp-B_trans
    distance = tf.reduce_sum(tf.square(diff),axis=-1)
    #to avoid rounding problems and keep it strict positive
    distance= tf.abs(distance)
    return distance



def nearest_neighbor_matrix(spatial_features, k=10):
    """
    Nearest neighbors matrix given spatial features.

    :param spatial_features: Spatial features of shape [B, N, S] where B = batch size, N = max examples in batch,
                             S = spatial features
    :param k: Max neighbors
    :return:
    """

    shape = spatial_features.get_shape().as_list()

    assert spatial_features.dtype == tf.float32 or spatial_features.dtype == tf.float64
    assert len(shape) == 3

    D = euclidean_squared(spatial_features, spatial_features)
    _, N = tf.nn.top_k(-D, k)
    return N


def nearest_neighbor_matrix_2(spatial_features, k=10):
    """
    Nearest neighbors matrix given spatial features.

    :param spatial_features: Spatial features of shape [B, N, S] where B = batch size, N = max examples in batch,
                             S = spatial features
    :param k: Max neighbors
    :return:
    """

    shape = spatial_features.get_shape().as_list()

    assert spatial_features.dtype == tf.float32 or spatial_features.dtype == tf.float64
    assert len(shape) == 3

    D = euclidean_squared(spatial_features, spatial_features)
    D, N = tf.nn.top_k(-D, k)
    return N, D


def indexing_tensor(spatial_features, k=10):

    shape_spatial_features = spatial_features.get_shape().as_list()

    n_batch = shape_spatial_features[0]
    n_max_entries = shape_spatial_features[1]

    # All of these tensors should be 3-dimensional
    assert len(shape_spatial_features) == 3

    # Neighbor matrix should be int as it should be used for indexing
    assert spatial_features.dtype == tf.float64 or spatial_features.dtype == tf.float32

    neighbor_matrix = nearest_neighbor_matrix(spatial_features, k)

    batch_range = tf.expand_dims(tf.expand_dims(tf.expand_dims(tf.range(0, n_batch), axis=1),axis=1), axis=1)
    batch_range = tf.tile(batch_range, [1,n_max_entries,k,1])
    expanded_neighbor_matrix = tf.expand_dims(neighbor_matrix, axis=3)

    _indexing_tensor = tf.concat([batch_range, expanded_neighbor_matrix], axis=3)

    return tf.cast(_indexing_tensor, tf.int64)


def indexing_tensor_2(spatial_features, k=10, n_batch=-1):

    shape_spatial_features = spatial_features.get_shape().as_list()
    generate_batch=True
    if n_batch<=0:
        n_batch = shape_spatial_features[0]
        generate_batch=False
    n_max_entries = shape_spatial_features[1]

    # All of these tensors should be 3-dimensional
    assert len(shape_spatial_features) == 3

    # Neighbor matrix should be int as it should be used for indexing
    assert spatial_features.dtype == tf.float64 or spatial_features.dtype == tf.float32

    neighbor_matrix, distance_matrix = nearest_neighbor_matrix_2(spatial_features, k)

    batch_range = tf.expand_dims(tf.expand_dims(tf.expand_dims(tf.range(0, n_batch), axis=1),axis=1), axis=1)
    batch_range = tf.tile(batch_range, [1,n_max_entries,k,1])
    expanded_neighbor_matrix = tf.expand_dims(neighbor_matrix, axis=3)
    
    if generate_batch:
        expanded_neighbor_matrix = tf.tile(expanded_neighbor_matrix,[n_batch,1,1,1])

    _indexing_tensor = tf.concat([batch_range, expanded_neighbor_matrix], axis=3)

    return tf.cast(_indexing_tensor, tf.int64), distance_matrix


def n_range_tensor(dims):
    assert type(dims) is list
    assert len(dims) != 0

    n_range_tensor = []
    for i in range(len(dims)):
        range_in_this_dim = tf.range(dims[i])
        for j in range(len(dims)):
            if j != i:
                range_in_this_dim = tf.expand_dims(range_in_this_dim, axis=j)
        tile_vector = dims[:]
        tile_vector[i] = 1
        range_in_this_dim = tf.tile(range_in_this_dim, tile_vector)
        range_in_this_dim = tf.expand_dims(range_in_this_dim, axis=len(dims))
        n_range_tensor.append(range_in_this_dim)

    return tf.concat(n_range_tensor, axis=len(dims))


def sort_last_dim_tensor(x):
    shape = x.shape.as_list()
    v, ind = tf.nn.top_k(x, shape[-1], sorted=False)
    

    ind = tf.expand_dims(ind, axis=-1)
    tensor_combine_with = n_range_tensor(shape)
    tensor_combine_with = tensor_combine_with[...,0:-1]
    _indexing_tensor = tf.concat([tensor_combine_with, ind], axis=-1)
    return _indexing_tensor


global saved_nd_range
if not ('saved_nd_range' in globals()):
    saved_nd_range = dict()


def sort_last_dim_tensor_save(x):
    global saved_nd_range
    shape = x.shape.as_list()
    v, ind = tf.nn.top_k(x, shape[-1])

    ind = tf.expand_dims(ind, axis=-1)

    # hash_value = hash(tuple(shape))
    # if hash_value in saved_nd_range:
    #     tensor_combine_with = saved_nd_range[hash_value]
    # else:
    tensor_combine_with = n_range_tensor(shape)
    tensor_combine_with = tensor_combine_with[...,0:-1]

    _indexing_tensor = tf.concat([tensor_combine_with, ind], axis=-1)
    return _indexing_tensor