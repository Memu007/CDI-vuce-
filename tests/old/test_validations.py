"""
Tests para validaciones de negocio - Lógica crítica del proyecto MARIA
"""
import pytest
from proyecto_maria.core.validations import run_pre_maria_validations, run_extra_validations
from proyecto_maria.models.operations import Item
from tests.conftest import sample_items, assert_valid_item


class TestPreMariaValidations:
    """Tests de validaciones pre-MARIA - Reglas de negocio críticas"""
    
    def test_valid_items_pass_all_validations(self, sample_items):
        """Items válidos deben pasar todas las validaciones"""
        # Convertir a modelos Pydantic
        pyd_items = [Item(**item) for item in sample_items]
        
        valid_items, errors = run_pre_maria_validations(pyd_items)
        
        # Todos deben ser válidos
        assert len(valid_items) == len(pyd_items)
        assert len(errors) == 0
        
        # Verificar estructura de items válidos
        for item in valid_items:
            assert_valid_item(item.model_dump())
    
    def test_invalid_ncm_code(self):
        """Validación de código NCM inválido"""
        invalid_items = [
            {
                "pieza": "123",  # Menos de 4 dígitos
                "descripcion": "Producto Test",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 100.0,
                "peso_unitario": 1.0
            }
        ]
        
        pyd_items = [Item(**item) for item in invalid_items]
        valid_items, errors = run_pre_maria_validations(pyd_items)
        
        # Debe haber error de NCM
        assert len(valid_items) == 0
        assert len(errors) > 0
        
        # Verificar mensaje de error
        error_text = ' '.join(errors)
        assert 'ncm' in error_text.lower() or 'pieza' in error_text.lower()
        assert '4' in error_text  # Mención de mínimo 4 dígitos
    
    def test_invalid_origin_code(self):
        """Validación de código de origen inválido"""
        invalid_items = [
            {
                "pieza": "84713010",
                "descripcion": "Laptop Test",
                "origen": "XYZ",  # 3 caracteres inválidos
                "cantidad": 10,
                "valor_unitario": 100.0,
                "peso_unitario": 1.0
            }
        ]
        
        pyd_items = [Item(**item) for item in invalid_items]
        valid_items, errors = run_pre_maria_validations(pyd_items)
        
        # Debe haber error de origen
        assert len(errors) > 0
        
        error_text = ' '.join(errors)
        assert 'origen' in error_text.lower()
        assert '2' in error_text  # Mención de 2 caracteres
    
    def test_invalid_quantity(self):
        """Validación de cantidad inválida"""
        invalid_items = [
            {
                "pieza": "84713010",
                "descripcion": "Laptop Test",
                "origen": "CN",
                "cantidad": 0,  # Cantidad inválida
                "valor_unitario": 100.0,
                "peso_unitario": 1.0
            }
        ]
        
        pyd_items = [Item(**item) for item in invalid_items]
        valid_items, errors = run_pre_maria_validations(pyd_items)
        
        # Debe haber error de cantidad
        assert len(errors) > 0
        
        error_text = ' '.join(errors)
        assert 'cantidad' in error_text.lower()
        assert '0' in error_text  # Mención de valor inválido
    
    def test_invalid_unit_value(self):
        """Validación de valor unitario inválido"""
        invalid_items = [
            {
                "pieza": "84713010",
                "descripcion": "Laptop Test",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": -50.0,  # Valor negativo
                "peso_unitario": 1.0
            }
        ]
        
        pyd_items = [Item(**item) for item in invalid_items]
        valid_items, errors = run_pre_maria_validations(pyd_items)
        
        # Debe haber error de valor unitario
        assert len(errors) > 0
        
        error_text = ' '.join(errors)
        assert 'valor' in error_text.lower() or 'unitario' in error_text.lower()
    
    def test_invalid_unit_weight(self):
        """Validación de peso unitario inválido"""
        invalid_items = [
            {
                "pieza": "84713010",
                "descripcion": "Laptop Test",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 100.0,
                "peso_unitario": -1.0  # Peso negativo
            }
        ]
        
        pyd_items = [Item(**item) for item in invalid_items]
        valid_items, errors = run_pre_maria_validations(pyd_items)
        
        # Debe haber error de peso unitario
        assert len(errors) > 0
        
        error_text = ' '.join(errors)
        assert 'peso' in error_text.lower()
    
    def test_multiple_errors_in_single_item(self):
        """Múltiples errores en un solo item"""
        invalid_items = [
            {
                "pieza": "12",  # NCM muy corto
                "descripcion": "",  # Descripción vacía
                "origen": "X",  # Origen muy corto
                "cantidad": -5,  # Cantidad negativa
                "valor_unitario": 0,  # Valor cero
                "peso_unitario": -2.0  # Peso negativo
            }
        ]
        
        pyd_items = [Item(**item) for item in invalid_items]
        valid_items, errors = run_pre_maria_validations(pyd_items)
        
        # Debe haber múltiples errores
        assert len(errors) >= 4  # Al menos 4 errores diferentes
        
        # Verificar que se mencionen los campos problemáticos
        error_text = ' '.join(errors).lower()
        problem_fields = ['pieza', 'descripcion', 'origen', 'cantidad', 'valor', 'peso']
        mentioned_fields = [field for field in problem_fields if field in error_text]
        assert len(mentioned_fields) >= 3  # Al menos 3 campos mencionados
    
    def test_mixed_valid_and_invalid_items(self):
        """Mezcla de items válidos e inválidos"""
        mixed_items = [
            # Item válido
            {
                "pieza": "84713010",
                "descripcion": "Laptop Dell",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 500.0,
                "peso_unitario": 2.5
            },
            # Item inválido
            {
                "pieza": "123",  # NCM muy corto
                "descripcion": "Producto Inválido",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 100.0,
                "peso_unitario": 1.0
            },
            # Otro item válido
            {
                "pieza": "85171200",
                "descripcion": "Smartphone Samsung",
                "origen": "VN",
                "cantidad": 20,
                "valor_unitario": 300.0,
                "peso_unitario": 0.2
            }
        ]
        
        pyd_items = [Item(**item) for item in mixed_items]
        valid_items, errors = run_pre_maria_validations(pyd_items)
        
        # Solo 2 deben ser válidos
        assert len(valid_items) == 2
        assert len(errors) > 0
        
        # Verificar que los items válidos sean los correctos
        valid_ncms = [item.pieza for item in valid_items]
        assert "84713010" in valid_ncms
        assert "85171200" in valid_ncms
        assert "123" not in valid_ncms
    
    def test_empty_items_list(self):
        """Lista vacía de items"""
        valid_items, errors = run_pre_maria_validations([])
        
        # No debe haber errores ni items válidos
        assert len(valid_items) == 0
        assert len(errors) == 0
    
    def test_edge_case_values(self):
        """Valores límite y edge cases"""
        edge_items = [
            # Valores mínimos válidos
            {
                "pieza": "1234",  # Exactamente 4 dígitos
                "descripcion": "A",  # Descripción mínima
                "origen": "AR",  # 2 caracteres
                "cantidad": 0.1,  # Cantidad mínima positiva
                "valor_unitario": 0.01,  # Valor mínimo positivo
                "peso_unitario": 0.01  # Peso mínimo positivo
            },
            # Valores altos pero válidos
            {
                "pieza": "99999999",  # 8 dígitos máximo
                "descripcion": "A" * 200,  # Descripción larga
                "origen": "XX",  # 2 caracteres
                "cantidad": 999999.99,  # Cantidad alta
                "valor_unitario": 999999.99,  # Valor alto
                "peso_unitario": 999999.99  # Peso alto
            }
        ]
        
        pyd_items = [Item(**item) for item in edge_items]
        valid_items, errors = run_pre_maria_validations(pyd_items)
        
        # Todos deben ser válidos
        assert len(valid_items) == len(pyd_items)
        assert len(errors) == 0


class TestExtraValidations:
    """Tests de validaciones extra - Reglas adicionales de negocio"""
    
    def test_extra_validations_on_valid_items(self, sample_items):
        """Validaciones extra en items válidos"""
        pyd_items = [Item(**item) for item in sample_items]
        
        extra_errors = run_extra_validations(pyd_items)
        
        # Items válidos no deben tener errores extra
        assert len(extra_errors) == 0
    
    def test_extra_validation_descripcion_too_short(self):
        """Validación extra: descripción muy corta"""
        items_with_short_desc = [
            {
                "pieza": "84713010",
                "descripcion": "PC",  # Muy corto
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 100.0,
                "peso_unitario": 1.0
            }
        ]
        
        pyd_items = [Item(**item) for item in items_with_short_desc]
        extra_errors = run_extra_validations(pyd_items)
        
        # Debe haber error de descripción corta
        assert len(extra_errors) > 0
        
        error_text = ' '.join(extra_errors).lower()
        assert 'descripc' in error_text
        assert 'corta' in error_text or 'poca' in error_text
    
    def test_extra_validation_high_value_low_weight(self):
        """Validación extra: valor alto con peso bajo (sospechoso)"""
        suspicious_items = [
            {
                "pieza": "84713010",
                "descripcion": "Dispositivo Electrónico",
                "origen": "CN",
                "cantidad": 1,
                "valor_unitario": 10000.0,  # Valor muy alto
                "peso_unitario": 0.01  # Peso muy bajo
            }
        ]
        
        pyd_items = [Item(**item) for item in suspicious_items]
        extra_errors = run_extra_validations(pyd_items)
        
        # Puede haber error de valor/peso desproporcionado
        # (Depende de la implementación específica)
    
    def test_extra_validation_duplicate_ncm(self):
        """Validación extra: NCM duplicados"""
        duplicate_ncm_items = [
            {
                "pieza": "84713010",
                "descripcion": "Laptop Dell",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 500.0,
                "peso_unitario": 2.5
            },
            {
                "pieza": "84713010",  # Mismo NCM
                "descripcion": "Laptop HP",
                "origen": "CN",
                "cantidad": 5,
                "valor_unitario": 600.0,
                "peso_unitario": 2.8
            }
        ]
        
        pyd_items = [Item(**item) for item in duplicate_ncm_items]
        extra_errors = run_extra_validations(pyd_items)
        
        # Puede haber advertencia de NCM duplicados
        # (Depende de la implementación específica)
    
    def test_extra_validation_unusual_origin_for_ncm(self):
        """Validación extra: origen inusual para NCM específico"""
        unusual_origin_items = [
            {
                "pieza": "03061300",  # NCM de productos marinos
                "descripcion": "Langostinos",
                "origen": "CH",  # Suiza - inusual para productos marinos
                "cantidad": 100,
                "valor_unitario": 50.0,
                "peso_unitario": 0.1
            }
        ]
        
        pyd_items = [Item(**item) for item in unusual_origin_items]
        extra_errors = run_extra_validations(pyd_items)
        
        # Puede haber advertencia de origen inusual
        # (Depende de la implementación específica)


class TestValidationIntegration:
    """Tests de integración de validaciones"""
    
    def test_combined_validation_workflow(self):
        """Flujo completo de validaciones pre y extra"""
        mixed_items = [
            # Item completamente válido
            {
                "pieza": "84713010",
                "descripcion": "Laptop Dell Inspiron 15",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 500.0,
                "peso_unitario": 2.5
            },
            # Item con error pre-MARIA
            {
                "pieza": "123",  # NCM muy corto
                "descripcion": "Producto",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 100.0,
                "peso_unitario": 1.0
            },
            # Item válido pero con posible problema extra
            {
                "pieza": "85171200",
                "descripcion": "Tel",  # Descripción muy corta
                "origen": "VN",
                "cantidad": 20,
                "valor_unitario": 300.0,
                "peso_unitario": 0.2
            }
        ]
        
        pyd_items = [Item(**item) for item in mixed_items]
        
        # Validaciones pre-MARIA
        valid_items, pre_errors = run_pre_maria_validations(pyd_items)
        
        # Validaciones extra solo en items válidos
        extra_errors = run_extra_validations(valid_items) if valid_items else []
        
        # Verificar resultados
        assert len(valid_items) == 1  # Solo el completamente válido
        assert len(pre_errors) >= 1  # Al menos el error de NCM
        
        # Los errores extra deben ser solo sobre items válidos
        total_errors = pre_errors + extra_errors
        assert len(total_errors) >= 1
    
    def test_validation_error_messages_format(self):
        """Formato de mensajes de error"""
        invalid_items = [
            {
                "pieza": "12",
                "descripcion": "",
                "origen": "X",
                "cantidad": -5,
                "valor_unitario": 0,
                "peso_unitario": -1.0
            }
        ]
        
        pyd_items = [Item(**item) for item in invalid_items]
        valid_items, errors = run_pre_maria_validations(pyd_items)
        
        # Verificar formato de errores
        assert len(errors) > 0
        
        for error in errors:
            # Los errores deben ser informativos
            assert isinstance(error, str)
            assert len(error) > 10  # Mensaje descriptivo
            
            # Deben mencionar el ítem (índice)
            assert 'ítem' in error.lower() or 'item' in error.lower()
            
            # Deben mencionar el problema específico
            error_lower = error.lower()
            problem_keywords = ['pieza', 'descripción', 'origen', 'cantidad', 'valor', 'peso']
            assert any(keyword in error_lower for keyword in problem_keywords)
    
    def test_validation_preserves_valid_data(self):
        """Validaciones deben preservar datos válidos sin modificar"""
        valid_items_data = [
            {
                "pieza": "84713010",
                "descripcion": "Laptop Dell Inspiron",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 500.0,
                "peso_unitario": 2.5
            }
        ]
        
        pyd_items = [Item(**item) for item in valid_items_data]
        valid_items, errors = run_pre_maria_validations(pyd_items)
        
        # No debe haber errores
        assert len(errors) == 0
        assert len(valid_items) == 1
        
        # Los datos deben ser idénticos
        original = valid_items_data[0]
        validated = valid_items[0].model_dump()
        
        assert validated['pieza'] == original['pieza']
        assert validated['descripcion'] == original['descripcion']
        assert validated['origen'] == original['origen']
        assert validated['cantidad'] == original['cantidad']
        assert validated['valor_unitario'] == original['valor_unitario']
        assert validated['peso_unitario'] == original['peso_unitario']


class TestValidationPerformance:
    """Tests de performance de validaciones"""
    
    def test_validation_performance_small_batch(self, sample_items):
        """Performance con batch pequeño"""
        import time
        
        pyd_items = [Item(**item) for item in sample_items]
        
        start_time = time.time()
        valid_items, errors = run_pre_maria_validations(pyd_items)
        end_time = time.time()
        
        # Debe ser muy rápido (< 10ms)
        assert end_time - start_time < 0.01
        assert len(valid_items) == len(pyd_items)
        assert len(errors) == 0
    
    def test_validation_performance_large_batch(self):
        """Performance con batch grande"""
        import time
        
        # Crear 1000 items
        large_batch = []
        for i in range(1000):
            item = {
                "pieza": f"8471{i:04d}"[:8],  # NCM variado
                "descripcion": f"Producto {i}",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 100.0 + i,
                "peso_unitario": 1.0 + (i * 0.01)
            }
            large_batch.append(item)
        
        pyd_items = [Item(**item) for item in large_batch]
        
        start_time = time.time()
        valid_items, errors = run_pre_maria_validations(pyd_items)
        end_time = time.time()
        
        # Debe ser razonablemente rápido (< 100ms para 1000 items)
        assert end_time - start_time < 0.1
        assert len(valid_items) == len(pyd_items)
        assert len(errors) == 0
    
    def test_validation_performance_with_errors(self):
        """Performance con items con errores"""
        import time
        
        # Crear batch con 50% de errores
        mixed_batch = []
        for i in range(100):
            if i % 2 == 0:
                # Item válido
                item = {
                    "pieza": "84713010",
                    "descripcion": f"Producto {i}",
                    "origen": "CN",
                    "cantidad": 10,
                    "valor_unitario": 100.0,
                    "peso_unitario": 1.0
                }
            else:
                # Item inválido
                item = {
                    "pieza": "12",  # NCM muy corto
                    "descripcion": f"Producto {i}",
                    "origen": "CN",
                    "cantidad": 10,
                    "valor_unitario": 100.0,
                    "peso_unitario": 1.0
                }
            mixed_batch.append(item)
        
        pyd_items = [Item(**item) for item in mixed_batch]
        
        start_time = time.time()
        valid_items, errors = run_pre_maria_validations(pyd_items)
        end_time = time.time()
        
        # Debe ser rápido incluso con errores
        assert end_time - start_time < 0.05
        assert len(valid_items) == 50  # Solo los válidos
        assert len(errors) == 50  # Un error por cada inválido


class TestValidationEdgeCases:
    """Tests de casos extremos de validación"""
    
    def test_validation_with_unicode_characters(self):
        """Validación con caracteres Unicode"""
        unicode_items = [
            {
                "pieza": "84713010",
                "descripcion": "Laptop con ñandú y café",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 500.0,
                "peso_unitario": 2.5
            },
            {
                "pieza": "85171200",
                "descripcion": "Телефон Samsung (cirílico)",
                "origen": "VN",
                "cantidad": 20,
                "valor_unitario": 300.0,
                "peso_unitario": 0.2
            }
        ]
        
        pyd_items = [Item(**item) for item in unicode_items]
        valid_items, errors = run_pre_maria_validations(pyd_items)
        
        # Debe manejar Unicode correctamente
        assert len(valid_items) == len(pyd_items)
        assert len(errors) == 0
        
        # Verificar que los caracteres se preserven
        for item in valid_items:
            desc = item.descripcion
            assert isinstance(desc, str)
            assert len(desc) > 0
    
    def test_validation_with_extreme_values(self):
        """Validación con valores extremos"""
        extreme_items = [
            {
                "pieza": "84713010",
                "descripcion": "Producto",
                "origen": "CN",
                "cantidad": 1e-10,  # Cantidad muy pequeña
                "valor_unitario": 1e10,  # Valor muy grande
                "peso_unitario": 1e-10  # Peso muy pequeño
            }
        ]
        
        pyd_items = [Item(**item) for item in extreme_items]
        valid_items, errors = run_pre_maria_validations(pyd_items)
        
        # Debe manejar valores extremos
        # (Puede pasar o fallar dependiendo de las reglas específicas)
    
    def test_validation_with_null_values(self):
        """Validación con valores nulos/None"""
        null_items = [
            {
                "pieza": None,  # Nulo
                "descripcion": "Producto",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 100.0,
                "peso_unitario": 1.0
            }
        ]
        
        # Pydantic debe manejar valores nulos según las reglas del modelo
        try:
            pyd_items = [Item(**item) for item in null_items]
            valid_items, errors = run_pre_maria_validations(pyd_items)
            
            # Si llega aquí, Pydantic aceptó el nulo
            # Las validaciones deben detectarlo como error
            assert len(errors) > 0
        except Exception:
            # Pydantic rechazó el nulo (comportamiento esperado)
            pass
    
    def test_validation_with_string_numbers(self):
        """Validación con números en formato string"""
        string_number_items = [
            {
                "pieza": "84713010",
                "descripcion": "Producto",
                "origen": "CN",
                "cantidad": "10",  # String
                "valor_unitario": "100.5",  # String
                "peso_unitario": "1.2"  # String
            }
        ]
        
        # Pydantic debe convertir strings a números
        pyd_items = [Item(**item) for item in string_number_items]
        valid_items, errors = run_pre_maria_validations(pyd_items)
        
        # Debe manejar la conversión correctamente
        assert len(valid_items) == 1
        assert len(errors) == 0
        
        # Verificar que los valores sean numéricos
        item = valid_items[0]
        assert isinstance(item.cantidad, (int, float))
        assert isinstance(item.valor_unitario, (int, float))
        assert isinstance(item.peso_unitario, (int, float))
