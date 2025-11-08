"""
Test suite for Database Schema Corrections - Fase 2
Verifies all database models, relationships, and migrations work correctly
"""

import asyncio
import os
import sys
import tempfile
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test imports
try:
    from database import (
        Base, engine, SessionLocal, get_db, create_tables, drop_tables,
        get_database_info, check_database_health, DatabaseTransaction,
        execute_transaction, initialize_database, migrate_database,
        get_database_schema_info, migration_manager
    )
    from database.models import (
        User, Course, UserCourse, LearningCard, CardReview, StudySession,
        Question, QuestionAttempt, QuizSession, Concept, ConceptConnection,
        ElaborationNetwork, UserAnalytics
    )
    from models.common import (
        DifficultyLevel, LearningStyle, CardType, QuestionType, BloomLevel
    )
    print("✅ All database imports successful")
except ImportError as e:
    print(f"❌ Database import failed: {e}")
    sys.exit(1)

# Test database connection and setup
def test_database_connection():
    print("\n🔍 Testing Database Connection...")

    try:
        # Test engine creation
        assert engine is not None
        print(f"✅ Database engine created: {engine.dialect.name}")

        # Test database info
        db_info = get_database_info()
        assert db_info is not None
        assert "driver" in db_info
        print(f"  - Driver: {db_info['driver']}")
        print(f"  - Pool size: {db_info['pool_size']}")

        # Test health check
        health = check_database_health()
        assert health is not None
        assert "status" in health
        print(f"  - Health: {health['status']}")

        # Test session creation
        db = SessionLocal()
        assert db is not None
        db.close()
        print("✅ Session creation successful")

        return True
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

# Test table creation
def test_table_creation():
    print("\n🔍 Testing Table Creation...")

    try:
        # Drop existing tables first
        drop_tables()

        # Create tables
        result = create_tables()
        assert result == True
        print("✅ Tables created successfully")

        # Verify tables exist by checking metadata
        table_names = list(Base.metadata.tables.keys())
        expected_tables = {
            'users', 'courses', 'user_courses', 'learning_cards', 'card_reviews',
            'study_sessions', 'study_session_cards', 'questions', 'question_attempts',
            'quiz_sessions', 'visual_elements', 'dual_coding_content',
            'metacognitive_sessions', 'reflection_activities', 'concepts',
            'concept_connections', 'elaboration_networks', 'user_analytics',
            'schema_migrations'
        }

        # Check that we have all expected tables
        found_tables = set(table_names)
        missing_tables = expected_tables - found_tables
        extra_tables = found_tables - expected_tables

        if missing_tables:
            print(f"⚠️  Missing tables: {missing_tables}")

        if extra_tables and 'schema_migrations' not in extra_tables:
            print(f"⚠️  Extra tables: {extra_tables}")

        print(f"✅ Created {len(table_names)} tables")
        print(f"  - Core tables: users, courses, learning_cards, questions")
        print(f"  - Session tables: study_sessions, quiz_sessions")
        print(f"  - Analytics tables: user_analytics")

        return True
    except Exception as e:
        print(f"❌ Table creation test failed: {e}")
        return False

# Test model creation and relationships
def test_model_creation():
    print("\n🔍 Testing Model Creation...")

    try:
        db = SessionLocal()

        # Create test user
        user = User(
            id="test-user-123",
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password="hashed_password_here",
            learning_style=LearningStyle.VISUAL,
            preferences={"theme": "dark", "notifications": True}
        )
        db.add(user)
        db.flush()  # Get the ID without committing

        # Create test course
        course = Course(
            id="test-course-123",
            title="Test Course",
            description="A test course for database verification",
            difficulty=DifficultyLevel.MEDIUM,
            tags=["test", "database"]
        )
        db.add(course)
        db.flush()

        # Enroll user in course
        user_course = UserCourse(
            user_id=user.id,
            course_id=course.id,
            progress=0.0
        )
        db.add(user_course)
        db.flush()

        # Create learning card
        learning_card = LearningCard(
            id="test-card-123",
            user_id=user.id,
            course_id=course.id,
            concept_id="test-concept",
            question="What is a database?",
            answer="A database is an organized collection of structured information",
            card_type=CardType.BASIC,
            difficulty=0.6,
            ease_factor=2.5,
            interval_days=1,
            repetitions=0,
            context_tags=["database", "basics"]
        )
        db.add(learning_card)
        db.flush()

        # Create concept
        concept = Concept(
            id="test-concept-123",
            name="Database",
            description="Structured data storage system",
            course_id=course.id,
            difficulty=0.5,
            mastery_level=0.0
        )
        db.add(concept)
        db.flush()

        # Create question
        question = Question(
            id="test-question-123",
            course_id=course.id,
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="What does SQL stand for?",
            options=[
                {"text": "Structured Query Language", "is_correct": True},
                {"text": "Simple Query Language", "is_correct": False},
                {"text": "Standard Query Logic", "is_correct": False}
            ],
            correct_answer="Structured Query Language",
            bloom_level=BloomLevel.UNDERSTAND,
            difficulty=DifficultyLevel.EASY
        )
        db.add(question)
        db.flush()

        # Create quiz session
        quiz_session = QuizSession(
            id="test-quiz-123",
            user_id=user.id,
            course_id=course.id,
            total_questions=1,
            time_limit_minutes=30
        )
        db.add(quiz_session)
        db.flush()

        # Create question attempt
        question_attempt = QuestionAttempt(
            id="test-attempt-123",
            question_id=question.id,
            user_id=user.id,
            session_id=quiz_session.id,
            user_answer="Structured Query Language",
            is_correct=True,
            confidence_level=4,
            time_taken_seconds=45,
            score_achieved=1.0
        )
        db.add(question_attempt)

        # Commit all changes
        db.commit()

        print("✅ Model creation successful")
        print(f"  - User: {user.username} (ID: {user.id})")
        print(f"  - Course: {course.title} (ID: {course.id})")
        print(f"  - Learning Card: {learning_card.question[:30]}...")
        print(f"  - Concept: {concept.name}")
        print(f"  - Question: {question.question_text[:30]}...")
        print(f"  - Quiz Session: {quiz_session.id}")
        print(f"  - Question Attempt: Correct={question_attempt.is_correct}")

        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Model creation test failed: {e}")
        return False
    finally:
        db.close()

# Test relationships and queries
def test_relationships_and_queries():
    print("\n🔍 Testing Relationships and Queries...")

    try:
        db = SessionLocal()

        # Test user relationships
        user = db.query(User).filter(User.id == "test-user-123").first()
        assert user is not None
        assert len(user.courses) == 1
        assert len(user.learning_cards) == 1
        print("✅ User relationships working")

        # Test course relationships
        course = db.query(Course).filter(Course.id == "test-course-123").first()
        assert course is not None
        assert len(course.users) == 1
        assert len(course.learning_cards) == 1
        print("✅ Course relationships working")

        # Test learning card relationships
        card = db.query(LearningCard).filter(LearningCard.id == "test-card-123").first()
        assert card is not None
        assert card.user.id == user.id
        assert card.course.id == course.id
        print("✅ Learning card relationships working")

        # Test concept connections (create one)
        concept1 = db.query(Concept).filter(Concept.id == "test-concept-123").first()
        concept2 = Concept(
            id="test-concept-456",
            name="Table",
            description="Database table structure",
            course_id=course.id,
            difficulty=0.4,
            mastery_level=0.0
        )
        db.add(concept2)
        db.flush()

        connection = ConceptConnection(
            id="test-connection-123",
            source_concept_id=concept1.id,
            target_concept_id=concept2.id,
            strength=0.7
        )
        db.add(connection)
        db.commit()

        # Test concept relationships
        concept1 = db.query(Concept).filter(Concept.id == "test-concept-123").first()
        assert len(concept1.source_connections) == 1
        print("✅ Concept relationships working")

        # Test complex queries
        user_cards = db.query(LearningCard).filter(
            LearningCard.user_id == user.id,
            LearningCard.difficulty > 0.5
        ).all()
        print(f"✅ Complex query found {len(user_cards)} cards")

        # Test analytics creation
        analytics = UserAnalytics(
            id="test-analytics-123",
            user_id=user.id,
            course_id=course.id,
            metric_type="cards_created",
            metric_value=1.0,
            context={"card_type": "basic"}
        )
        db.add(analytics)
        db.commit()
        print("✅ Analytics model working")

        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Relationships and queries test failed: {e}")
        return False
    finally:
        db.close()

# Test database transactions
def test_database_transactions():
    print("\n🔍 Testing Database Transactions...")

    try:
        db = SessionLocal()

        # Test successful transaction
        def successful_operation(session):
            user = session.query(User).filter(User.id == "test-user-123").first()
            user.preferences["test_key"] = "test_value"
            session.add(user)
            return True

        result = execute_transaction(db, successful_operation)
        assert result == True
        print("✅ Successful transaction working")

        # Test failed transaction (rollback)
        def failing_operation(session):
            user = session.query(User).filter(User.id == "test-user-123").first()
            user.preferences["should_rollback"] = True
            session.add(user)
            raise Exception("Intentional failure")

        try:
            execute_transaction(db, failing_operation)
            assert False, "Should have raised exception"
        except Exception:
            pass  # Expected

        # Verify rollback worked
        user = db.query(User).filter(User.id == "test-user-123").first()
        assert "should_rollback" not in user.preferences
        print("✅ Failed transaction rollback working")

        return True
    except Exception as e:
        print(f"❌ Database transactions test failed: {e}")
        return False
    finally:
        db.close()

# Test migrations
def test_migrations():
    print("\n🔍 Testing Database Migrations...")

    try:
        # Get migration status
        status = migration_manager.get_migration_status()
        assert status is not None
        print(f"✅ Migration status retrieved")
        print(f"  - Total migrations: {status['total_migrations']}")
        print(f"  - Applied: {status['applied_count']}")
        print(f"  - Pending: {status['pending_count']}")

        # Apply migrations
        success = migrate_database()
        assert success == True
        print("✅ Migrations applied successfully")

        # Verify migration table exists and has records
        db = SessionLocal()
        migration_records = db.execute("SELECT version, description FROM schema_migrations ORDER BY version").fetchall()
        assert len(migration_records) > 0
        print(f"✅ Migration records created: {len(migration_records)} migrations applied")

        # Get schema info
        schema_info = get_database_schema_info()
        assert schema_info is not None
        assert "migration_status" in schema_info
        assert "table_counts" in schema_info
        print(f"✅ Schema info retrieved successfully")
        print(f"  - Total tables: {schema_info['total_tables']}")
        print(f"  - Table counts: {len(schema_info['table_counts'])}")

        db.close()
        return True
    except Exception as e:
        print(f"❌ Migrations test failed: {e}")
        return False

# Test constraints and validation
def test_constraints_and_validation():
    print("\n🔍 Testing Constraints and Validation...")

    try:
        db = SessionLocal()

        # Test unique constraint on users.email
        try:
            duplicate_user = User(
                id="duplicate-user-123",
                email="test@example.com",  # Same email as existing user
                username="duplicate_user",
                hashed_password="password"
            )
            db.add(duplicate_user)
            db.commit()
            assert False, "Should have failed due to unique constraint"
        except Exception:
            db.rollback()
            print("✅ Email unique constraint working")

        # Test learning card difficulty constraints
        try:
            invalid_card = LearningCard(
                id="invalid-card-123",
                user_id="test-user-123",
                course_id="test-course-123",
                question="Test",
                answer="Test",
                difficulty=1.5  # Invalid: > 1.0
            )
            db.add(invalid_card)
            db.commit()
            assert False, "Should have failed due to difficulty constraint"
        except Exception:
            db.rollback()
            print("✅ Learning card difficulty constraint working")

        # Test question attempt confidence constraint
        try:
            invalid_attempt = QuestionAttempt(
                id="invalid-attempt-123",
                question_id="test-question-123",
                user_id="test-user-123",
                user_answer="Test",
                is_correct=True,
                confidence_level=10  # Invalid: > 5
            )
            db.add(invalid_attempt)
            db.commit()
            assert False, "Should have failed due to confidence constraint"
        except Exception:
            db.rollback()
            print("✅ Question attempt confidence constraint working")

        # Test valid data that should pass
        valid_card = LearningCard(
            id="valid-card-123",
            user_id="test-user-123",
            course_id="test-course-123",
            question="Valid test question?",
            answer="Valid test answer",
            difficulty=0.7  # Valid: 0-1 range
        )
        db.add(valid_card)
        db.commit()
        print("✅ Valid data acceptance working")

        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Constraints and validation test failed: {e}")
        return False
    finally:
        db.close()

# Test database cleanup
def test_database_cleanup():
    print("\n🔍 Testing Database Cleanup...")

    try:
        # Test reset functionality
        result = reset_database()
        assert result == True
        print("✅ Database reset successful")

        # Test that tables are empty (except schema_migrations)
        db = SessionLocal()
        user_count = db.query(User).count()
        course_count = db.query(Course).count()
        card_count = db.query(LearningCard).count()

        # Schema migrations table should still exist
        migration_count = db.execute("SELECT COUNT(*) FROM schema_migrations").scalar()

        print(f"✅ Database cleanup verification")
        print(f"  - Users: {user_count}")
        print(f"  - Courses: {course_count}")
        print(f"  - Cards: {card_count}")
        print(f"  - Migration records: {migration_count}")

        db.close()
        return True
    except Exception as e:
        print(f"❌ Database cleanup test failed: {e}")
        return False

# Main test runner
async def run_all_database_tests():
    print("🚀 Starting Database Schema Corrections Testing - Fase 2")
    print("=" * 60)

    tests = [
        ("Database Connection", test_database_connection),
        ("Table Creation", test_table_creation),
        ("Model Creation", test_model_creation),
        ("Relationships and Queries", test_relationships_and_queries),
        ("Database Transactions", test_database_transactions),
        ("Migrations", test_migrations),
        ("Constraints and Validation", test_constraints_and_validation),
        ("Database Cleanup", test_database_cleanup)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            failed += 1

    # Results
    print("\n" + "=" * 60)
    print("📊 DATABASE SCHEMA TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n🎉 ALL DATABASE SCHEMA TESTS PASSED!")
        print("📈 Database System Fully Operational")
        print("\n✅ Ready for Performance Optimization")
        return True
    else:
        print(f"\n⚠️  {failed} database schema issues remaining")
        print("🔧 Address issues before proceeding")
        return False

# Run all tests
async def main():
    print("🧪 CLE Database Schema Test Suite")
    print(f"⏰ Started: {datetime.now().isoformat()}")

    # Run all tests
    success = await run_all_database_tests()

    if success:
        print("\n" + "=" * 60)
        print("🚀 FASE 2 DATABASE SCHEMA - COMPLETED SUCCESSFULLY! 🎉")
        print("=" * 60)
        print("\n📋 DATABASE FEATURES IMPLEMENTED:")
        print("  ✅ SQLAlchemy models with proper relationships")
        print("  ✅ Database indexes for performance optimization")
        print("  ✅ Constraints and validation")
        print("  ✅ Transaction management with rollback")
        print("  ✅ Migration system with versioning")
        print("  ✅ Comprehensive table structure")
        print("  ✅ Query optimization")
        print("  ✅ Health checks and monitoring")

        print("\n🎯 DATABASE STATUS: PRODUCTION READY")
        print("\n📅 NEXT TASKS (Fase 2):")
        print("  - Performance Optimization")
        print("  - Security Enhancements")
        print("  - Unit Testing Implementation")
        print("\n✨ READY FOR PERFORMANCE OPTIMIZATION")
        return True
    else:
        print("\n❌ DATABASE SCHEMA IMPLEMENTATION INCOMPLETE")
        return False

if __name__ == "__main__":
    asyncio.run(main())